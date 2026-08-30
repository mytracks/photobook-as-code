"""
The batch operation: walking every item of the book once, inserting a
formatted date at each new day and/or a reverse-geocoded location on every
GPS-tagged photo, per user-chosen settings - see the `add-batch-labeling`
change's proposal.md and design.md for the full rationale.

Runs as a background thread (started by the Flask route in app.py) so the
browser isn't held on a single request for the run's full duration, which
can be minutes once Nominatim's 1 req/sec rate limit is in play. Each item
is saved to the YAML file as soon as it's processed - see
`yaml_store.save_photo_text`/`insert_new_title_entry`/`prepend_to_title_entry`
- so a cancelled or interrupted run leaves no partial edits, and simply
re-running (with the skip setting) is how a run is resumed.
"""

import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set

from . import geocoding, yaml_store
from .data import EditorData, PhotoDirectoryCache, load_editor_data
from .date_formatting import format_batch_date

DATE_DESTINATION_TEXT_LABEL = "text-label"
DATE_DESTINATION_TITLE = "title"

SKIP_MODE_SKIP = "skip"
SKIP_MODE_APPEND = "append"

STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"
STATUS_ERROR = "error"


class BatchAlreadyRunningError(Exception):
    """Raised by start_batch_job when a job is already running."""

    def __init__(self, job_id: str):
        super().__init__(f"A batch operation ({job_id}) is already running")
        self.job_id = job_id


@dataclass
class BatchSettings:
    """The user's choices from the batch settings page."""

    date_enabled: bool
    date_destination: str  # DATE_DESTINATION_TEXT_LABEL or DATE_DESTINATION_TITLE
    geocode_enabled: bool
    geocode_strict: bool  # True = POI-only, False = POI-with-city-fallback
    skip_mode: str  # SKIP_MODE_SKIP or SKIP_MODE_APPEND

    def validate(self) -> None:
        if not self.date_enabled and not self.geocode_enabled:
            raise ValueError("At least one of date insertion or reverse-geocoding must be enabled")
        if self.date_destination not in (DATE_DESTINATION_TEXT_LABEL, DATE_DESTINATION_TITLE):
            raise ValueError(f"Invalid date_destination: {self.date_destination!r}")
        if self.skip_mode not in (SKIP_MODE_SKIP, SKIP_MODE_APPEND):
            raise ValueError(f"Invalid skip_mode: {self.skip_mode!r}")


@dataclass
class JobState:
    """
    Progress and results of one batch run. Counters are only ever written
    by the single worker thread that owns this job; other threads only
    read them (via to_dict), which is safe without extra locking under
    CPython's GIL for simple attribute reads/writes.
    """

    job_id: str
    total: int
    accept_language: str
    processed: int = 0
    updated: int = 0
    skipped_existing: int = 0
    skipped_no_poi: int = 0
    skipped_duplicate_location: int = 0
    failed: int = 0
    current_label: str = ""
    status: str = STATUS_RUNNING
    error_message: str = ""
    cancel_event: threading.Event = field(default_factory=threading.Event)
    # Resolved location texts already inserted so far this run, so a repeat
    # (e.g. two photos both resolving to "Fernsehturm") is only inserted
    # once - see _process_photo. Never persisted or shared across runs.
    used_location_texts: Set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "total": self.total,
            "processed": self.processed,
            "updated": self.updated,
            "skipped_existing": self.skipped_existing,
            "skipped_no_poi": self.skipped_no_poi,
            "skipped_duplicate_location": self.skipped_duplicate_location,
            "failed": self.failed,
            "current_label": self.current_label,
            "status": self.status,
            "error_message": self.error_message,
        }


def _current_text_labels(config_path: Path) -> list:
    """
    A fresh, current-on-disk view of text_labels, suitable for passing into
    yaml_store's save_photo_text/prepend_to_title_entry (which locate an
    entry by its index in this list, then apply that index to a document
    they load fresh themselves).

    This must be reloaded before every write within a batch run rather than
    reusing the job-start EditorData snapshot: an earlier write in the same
    run (e.g. a new title inserted before this entry) can shift later
    entries' positions in the file, and an index computed against a stale
    view would then land on the wrong entry.
    """
    return yaml_store.load_document(config_path).get("text_labels") or []


_jobs: Dict[str, JobState] = {}
_jobs_lock = threading.Lock()
_active_job_id: Optional[str] = None


def get_job(job_id: str) -> Optional[JobState]:
    with _jobs_lock:
        return _jobs.get(job_id)


def cancel_job(job_id: str) -> bool:
    """Request cancellation of a running job. Returns False if the job is
    unknown or already finished."""
    job = get_job(job_id)
    if job is None or job.status != STATUS_RUNNING:
        return False
    job.cancel_event.set()
    return True


def start_batch_job(
    config_path: Path,
    photo_cache: PhotoDirectoryCache,
    settings: BatchSettings,
    accept_language: str,
) -> str:
    """
    Validate settings, load a fresh EditorData snapshot, and start the batch
    as a background thread. Returns the new job's id.

    Raises BatchAlreadyRunningError if a batch is already running, and
    ValueError (via BatchSettings.validate) for invalid settings - both
    checked before any snapshot is loaded or thread started.
    """
    global _active_job_id

    settings.validate()

    with _jobs_lock:
        if _active_job_id is not None and _jobs[_active_job_id].status == STATUS_RUNNING:
            raise BatchAlreadyRunningError(_active_job_id)

        snapshot = load_editor_data(config_path, photo_cache=photo_cache)
        job_id = str(uuid.uuid4())
        job = JobState(job_id=job_id, total=snapshot.count, accept_language=accept_language)
        _jobs[job_id] = job
        _active_job_id = job_id

    thread = threading.Thread(
        target=_run_job, args=(job, config_path, snapshot, settings), daemon=True
    )
    thread.start()
    return job_id


def _run_job(
    job: JobState, config_path: Path, snapshot: EditorData, settings: BatchSettings
) -> None:
    try:
        for index in range(snapshot.count):
            if job.cancel_event.is_set():
                job.status = STATUS_CANCELLED
                return

            if snapshot.is_title(index):
                title_label = snapshot.title_at(index)
                job.current_label = title_label.title or title_label.timestamp.isoformat()
                _process_title_boundary(job, config_path, snapshot, index, title_label, settings)
            else:
                photo = snapshot.photo_at(index)
                job.current_label = photo.filename
                if settings.date_enabled and settings.date_destination == DATE_DESTINATION_TITLE:
                    _process_new_title_for_photo(job, config_path, snapshot, index, photo, settings)
                _process_photo(job, config_path, snapshot, index, photo, settings)

            job.processed += 1

        job.status = STATUS_DONE
    except Exception as e:  # noqa: BLE001 - a background thread has no other way to report this
        job.status = STATUS_ERROR
        job.error_message = str(e)
    finally:
        global _active_job_id
        with _jobs_lock:
            if _active_job_id == job.job_id:
                _active_job_id = None


def _process_title_boundary(
    job: JobState,
    config_path: Path,
    snapshot: EditorData,
    index: int,
    title_label,
    settings: BatchSettings,
) -> None:
    """Title-destination date insertion when this title already occupies a
    new-day boundary: skip/append against its own existing content."""
    if not (settings.date_enabled and settings.date_destination == DATE_DESTINATION_TITLE):
        return
    if not snapshot.is_new_day(index):
        return

    existing = title_label.title
    if existing and settings.skip_mode == SKIP_MODE_SKIP:
        job.skipped_existing += 1
        return

    date_text = format_batch_date(title_label.timestamp, job.accept_language)
    yaml_store.prepend_to_title_entry(config_path, _current_text_labels(config_path), title_label, date_text)
    job.updated += 1


def _process_new_title_for_photo(
    job: JobState,
    config_path: Path,
    snapshot: EditorData,
    index: int,
    photo,
    settings: BatchSettings,
) -> None:
    """Title-destination date insertion when this photo is a new-day
    boundary with no title already there: create a fresh title before it.
    Always writes - there is no pre-existing content to skip or append to."""
    if not snapshot.is_new_day(index):
        return

    date_text = format_batch_date(photo.sort_date, job.accept_language)
    document = yaml_store.load_document(config_path)
    yaml_store.insert_new_title_entry(document, photo, date_text)
    yaml_store.save_document(config_path, document)
    job.updated += 1


def _process_photo(
    job: JobState,
    config_path: Path,
    snapshot: EditorData,
    index: int,
    photo,
    settings: BatchSettings,
) -> None:
    """
    Text-label date insertion and/or reverse-geocoding for this photo's own
    caption, combined into a single write (date first, then the geocoded
    location) when both apply in this run - see design.md's "combine on the
    same photo" decision. The skip-or-append setting is evaluated once,
    against the caption's content before this run, and governs both.

    A resolved location text already used earlier in this run is withheld
    here (see JobState.used_location_texts) rather than inserted again,
    without affecting an unrelated date marker for this same photo.
    """
    wants_date_here = (
        settings.date_enabled
        and settings.date_destination == DATE_DESTINATION_TEXT_LABEL
        and snapshot.is_new_day(index)
    )
    wants_geocode_here = settings.geocode_enabled and snapshot.has_gps(index)

    if not wants_date_here and not wants_geocode_here:
        return

    label = snapshot.label_for(index)
    original_text = snapshot.text_for(index)
    pre_existing = bool(original_text)

    if pre_existing and settings.skip_mode == SKIP_MODE_SKIP:
        job.skipped_existing += 1
        return

    new_pieces = []

    if wants_date_here:
        new_pieces.append(format_batch_date(photo.sort_date, job.accept_language))

    if wants_geocode_here:
        lat, lon = photo.gps
        try:
            response = geocoding.reverse_geocode(lat, lon, accept_language=job.accept_language)
        except geocoding.GeocodingError:
            job.failed += 1
            response = None
        if response is not None:
            place = geocoding.resolve_place_name(response, strict=settings.geocode_strict)
            if place is None:
                job.skipped_no_poi += 1
            elif place in job.used_location_texts:
                job.skipped_duplicate_location += 1
            else:
                job.used_location_texts.add(place)
                new_pieces.append(place)

    if not new_pieces:
        return

    combined = "\n".join(([original_text] if pre_existing else []) + new_pieces)
    yaml_store.save_photo_text(config_path, _current_text_labels(config_path), photo, label, combined)
    job.updated += 1
