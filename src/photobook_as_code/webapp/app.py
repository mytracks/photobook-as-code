"""
Flask application for the text_labels web editor.
"""

import io
from pathlib import Path
from typing import Optional

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, url_for
from PIL import Image

from . import batch, geocoding, yaml_store
from .data import EditorData, PhotoDirectoryCache, load_editor_data

MAX_IMAGE_DIMENSION = 1600
JPEG_QUALITY = 85


def create_app(config_path: Path, photo_cache: Optional[PhotoDirectoryCache] = None) -> Flask:
    """Build the Flask app bound to a single photobook configuration file."""
    app = Flask(__name__)
    app.config["PHOTOBOOK_CONFIG_PATH"] = Path(config_path)
    if photo_cache is None:
        photo_cache = PhotoDirectoryCache()

    def _load_data_or_404(index: int) -> EditorData:
        data = load_editor_data(app.config["PHOTOBOOK_CONFIG_PATH"], photo_cache=photo_cache)
        if index < 0 or index >= data.count:
            abort(404)
        return data

    @app.get("/")
    def index():
        return redirect(url_for("view_item", index=0))

    @app.get("/items/<int:index>")
    def view_item(index: int):
        data = _load_data_or_404(index)

        common_context = dict(
            index=index,
            total=data.count,
            has_prev=index > 0,
            has_next=index < data.count - 1,
            date_display=data.display_date(index),
            date_taken_iso=data.date_taken_iso(index),
            is_new_day=data.is_new_day(index),
            has_gps=data.has_gps(index),
        )

        if data.is_title(index):
            return render_template(
                "editor.html",
                is_title=True,
                title_text=data.title_text_for(index),
                **common_context,
            )

        photo = data.photo_at(index)
        return render_template(
            "editor.html",
            is_title=False,
            filename=photo.filename,
            text=data.text_for(index),
            photo_width=photo.width,
            photo_height=photo.height,
            **common_context,
        )

    @app.get("/items/<int:index>/image")
    def item_image(index: int):
        data = _load_data_or_404(index)
        if data.is_title(index):
            abort(404)
        photo = data.photo_at(index)

        with Image.open(photo.path) as img:
            img = img.convert("RGB")
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=JPEG_QUALITY)
            buf.seek(0)

        return send_file(buf, mimetype="image/jpeg")

    @app.post("/items/<int:index>/text")
    def save_text(index: int):
        data = _load_data_or_404(index)
        if data.is_title(index):
            abort(400)

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
            abort(400)

        photo = data.photo_at(index)
        label = data.label_for(index)
        yaml_store.save_photo_text(
            app.config["PHOTOBOOK_CONFIG_PATH"],
            data.config.text_labels,
            photo,
            label,
            payload["text"],
        )

        return jsonify({"status": "ok"})

    @app.post("/items/<int:index>/title")
    def save_title(index: int):
        data = _load_data_or_404(index)
        if not data.is_title(index):
            abort(400)

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
            abort(400)

        label = data.title_at(index)
        yaml_store.save_title_text(
            app.config["PHOTOBOOK_CONFIG_PATH"],
            data.config.text_labels,
            label,
            payload["text"],
        )

        return jsonify({"status": "ok"})

    @app.post("/items/<int:index>/add-title")
    def add_title(index: int):
        data = _load_data_or_404(index)
        if data.is_title(index):
            abort(400)

        photo = data.photo_at(index)
        yaml_store.insert_new_title(app.config["PHOTOBOOK_CONFIG_PATH"], photo)

        # The new title takes the photo's old slot, immediately before it.
        return jsonify({"status": "ok", "index": index})

    @app.post("/items/<int:index>/reverse-geocode")
    def reverse_geocode_item(index: int):
        data = _load_data_or_404(index)
        if data.is_title(index):
            abort(400)

        photo = data.photo_at(index)
        if photo.gps is None:
            abort(400)

        lat, lon = photo.gps
        accept_language = request.headers.get("Accept-Language", "")

        try:
            response = geocoding.reverse_geocode(lat, lon, accept_language=accept_language)
        except geocoding.GeocodingError:
            return jsonify({
                "status": "error",
                "reason": "service_error",
                "message": "Reverse geocoding service is unavailable",
            }), 502

        place_name = geocoding.resolve_place_name(response)
        if place_name is None:
            return jsonify({
                "status": "error",
                "reason": "no_location_found",
                "message": "No location could be resolved for this photo",
            }), 404

        return jsonify({"status": "ok", "text": place_name})

    @app.get("/batch")
    def batch_settings():
        return render_template("batch.html")

    @app.post("/batch/start")
    def batch_start():
        form = request.form
        settings = batch.BatchSettings(
            date_enabled=form.get("date_enabled") == "on",
            date_destination=form.get("date_destination", batch.DATE_DESTINATION_TEXT_LABEL),
            geocode_enabled=form.get("geocode_enabled") == "on",
            geocode_strict=form.get("geocode_strictness") == "strict",
            skip_mode=form.get("skip_mode", batch.SKIP_MODE_SKIP),
        )
        accept_language = request.headers.get("Accept-Language", "")

        try:
            job_id = batch.start_batch_job(
                app.config["PHOTOBOOK_CONFIG_PATH"], photo_cache, settings, accept_language
            )
        except ValueError:
            abort(400)
        except batch.BatchAlreadyRunningError as e:
            # Send the user to the job that's already running instead of
            # failing the request outright.
            job_id = e.job_id

        return redirect(url_for("batch_progress", job_id=job_id))

    @app.get("/batch/progress/<job_id>")
    def batch_progress(job_id: str):
        if batch.get_job(job_id) is None:
            abort(404)
        return render_template("batch_progress.html", job_id=job_id)

    @app.get("/batch/status/<job_id>")
    def batch_status(job_id: str):
        job = batch.get_job(job_id)
        if job is None:
            abort(404)
        return jsonify(job.to_dict())

    @app.post("/batch/cancel/<job_id>")
    def batch_cancel(job_id: str):
        if batch.get_job(job_id) is None:
            abort(404)
        batch.cancel_job(job_id)
        return jsonify({"status": "ok"})

    @app.post("/items/<int:index>/delete-title")
    def delete_title(index: int):
        data = _load_data_or_404(index)
        if not data.is_title(index):
            abort(400)

        label = data.title_at(index)
        yaml_store.delete_title_entry(
            app.config["PHOTOBOOK_CONFIG_PATH"],
            data.config.text_labels,
            label,
        )

        # Everything after the deleted title shifts back by one, so the
        # item that follows it (if any) now occupies the same index.
        new_data = load_editor_data(app.config["PHOTOBOOK_CONFIG_PATH"], photo_cache=photo_cache)
        redirect_index = min(index, new_data.count - 1) if new_data.count > 0 else 0
        return jsonify({"status": "ok", "index": redirect_index})

    return app
