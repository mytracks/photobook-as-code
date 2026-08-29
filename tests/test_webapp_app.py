"""
Integration tests for the web editor's Flask routes.
"""

from pathlib import Path

from PIL import ExifTags, Image

import photobook_as_code.webapp.data as data_module
import photobook_as_code.webapp.geocoding as geocoding_module
from photobook_as_code.config import load_config
from photobook_as_code.webapp.app import create_app


def _make_photos_dir(tmp_path: Path) -> Path:
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    exif = Image.Exif()
    exif[36867] = "2025:06:14 10:00:00"  # DateTimeOriginal
    Image.new("RGB", (2000, 1500), color="white").save(photos_dir / "a.jpg", exif=exif.tobytes())
    Image.new("RGB", (2000, 1500), color="white").save(photos_dir / "b.jpg")
    return photos_dir


def _make_photos_dir_with_gps(tmp_path: Path) -> Path:
    """Like _make_photos_dir, but a.jpg also carries a GPS EXIF location."""
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    exif = Image.Exif()
    exif[36867] = "2025:06:14 10:00:00"  # DateTimeOriginal
    exif[ExifTags.IFD.GPSInfo] = {
        1: "N",
        2: (53.0, 33.0, 12.6),
        3: "E",
        4: (10.0, 0.0, 0.0),
    }
    Image.new("RGB", (2000, 1500), color="white").save(photos_dir / "a.jpg", exif=exif.tobytes())
    Image.new("RGB", (2000, 1500), color="white").save(photos_dir / "b.jpg")
    return photos_dir


def _write_config(tmp_path: Path, photos_dir: Path) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"photo_folders:\n  - {photos_dir}\n"
        "output:\n"
        "  size: A4\n"
        "layout:\n"
        "  photos_per_page: 2\n"
        "  order: alphabetical\n"
        "theme: clean\n"
        "text_labels:\n"
        '  - timestamp: "2020-01-01T00:00:00"\n'
        "    text: existing caption for a\n"
    )
    return config_path


def _write_config_with_title(tmp_path: Path, photos_dir: Path) -> Path:
    """
    A config whose photo order is [a.jpg, b.jpg] (alphabetical) with a title
    entry timestamped to land between them: after a.jpg's fixed 2025-06-14
    EXIF date, before b.jpg's no-EXIF fallback (its file's real creation
    time, always later than 2025-12-31 for this repo).
    """
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"photo_folders:\n  - {photos_dir}\n"
        "output:\n"
        "  size: A4\n"
        "layout:\n"
        "  photos_per_page: 2\n"
        "  order: alphabetical\n"
        "theme: clean\n"
        "text_labels:\n"
        '  - timestamp: "2020-01-01T00:00:00"\n'
        "    text: existing caption for a\n"
        '  - timestamp: "2025-12-31T00:00:00"\n'
        "    title: Existing Title\n"
    )
    return config_path


def _write_config_with_trailing_title(tmp_path: Path, photos_dir: Path) -> Path:
    """A config whose title is timestamped after every photo, so it is the last item."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"photo_folders:\n  - {photos_dir}\n"
        "output:\n"
        "  size: A4\n"
        "layout:\n"
        "  photos_per_page: 2\n"
        "  order: alphabetical\n"
        "theme: clean\n"
        "text_labels:\n"
        '  - timestamp: "2099-01-01T00:00:00"\n'
        "    title: Trailing Title\n"
    )
    return config_path


def make_client(tmp_path):
    photos_dir = _make_photos_dir(tmp_path)
    config_path = _write_config(tmp_path, photos_dir)
    app = create_app(config_path)
    app.config["TESTING"] = True
    return app.test_client(), config_path


def make_client_with_title(tmp_path):
    photos_dir = _make_photos_dir(tmp_path)
    config_path = _write_config_with_title(tmp_path, photos_dir)
    app = create_app(config_path)
    app.config["TESTING"] = True
    return app.test_client(), config_path


def make_client_with_trailing_title(tmp_path):
    photos_dir = _make_photos_dir(tmp_path)
    config_path = _write_config_with_trailing_title(tmp_path, photos_dir)
    app = create_app(config_path)
    app.config["TESTING"] = True
    return app.test_client(), config_path


def make_client_with_gps(tmp_path):
    photos_dir = _make_photos_dir_with_gps(tmp_path)
    config_path = _write_config(tmp_path, photos_dir)
    app = create_app(config_path)
    app.config["TESTING"] = True
    return app.test_client(), config_path


class TestNavigation:
    def test_root_redirects_to_first_photo(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.get("/")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/items/0")

    def test_view_first_photo_shows_existing_text(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.get("/items/0")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "a.jpg" in body
        assert "existing caption for a" in body
        assert 'id="nav-next"' in body

    def test_view_second_photo_shows_empty_text(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.get("/items/1")
        assert response.status_code == 200
        assert "b.jpg" in response.get_data(as_text=True)

    def test_out_of_range_index_is_404(self, tmp_path):
        client, _ = make_client(tmp_path)
        assert client.get("/items/99").status_code == 404
        assert client.get("/items/-1").status_code == 404

    def test_photo_with_exif_date_shows_formatted_date(self, tmp_path):
        # Formatting itself now happens client-side (locale-aware, see
        # editor.js); the server's job is to expose the raw timestamp for
        # JS to format, plus a plain-English fallback for no-JS clients.
        client, _ = make_client(tmp_path)
        body = client.get("/items/0").get_data(as_text=True)
        assert 'data-date="2025-06-14T10:00:00"' in body
        assert "Saturday, June 14, 2025 · 10:00" in body

    def test_photo_without_exif_date_shows_filename_instead(self, tmp_path):
        client, _ = make_client(tmp_path)
        body = client.get("/items/1").get_data(as_text=True)
        assert "b.jpg" in body
        assert "data-date=" not in body


class TestHeaderControls:
    def test_nav_controls_disabled_at_first_item(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)  # merged order: [a.jpg, title, b.jpg]
        body = client.get("/items/0").get_data(as_text=True)
        assert 'id="nav-prev" aria-disabled="true"' in body
        assert 'id="nav-next" href=' in body

    def test_nav_controls_disabled_at_last_item(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        body = client.get("/items/2").get_data(as_text=True)
        assert 'id="nav-next" aria-disabled="true"' in body
        assert 'id="nav-prev" href=' in body

    def test_nav_controls_both_enabled_in_the_middle(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        body = client.get("/items/1").get_data(as_text=True)
        assert 'id="nav-prev" href=' in body
        assert 'id="nav-next" href=' in body
        assert "aria-disabled" not in body

    def test_position_control_shows_index_and_total(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        body = client.get("/items/1").get_data(as_text=True)
        assert '<button type="button" id="position-display" class="position">2 / 3</button>' in body

    def test_position_control_is_a_focusable_button_not_a_span(self, tmp_path):
        client, _ = make_client(tmp_path)
        body = client.get("/items/0").get_data(as_text=True)
        assert '<span class="position">' not in body
        assert '<button type="button" id="position-display" class="position">' in body


class TestPhotoImage:
    def test_image_is_served_as_jpeg(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.get("/items/0/image")
        assert response.status_code == 200
        assert response.mimetype == "image/jpeg"

    def test_image_out_of_range_is_404(self, tmp_path):
        client, _ = make_client(tmp_path)
        assert client.get("/items/99/image").status_code == 404


class TestSaveText:
    def test_saving_new_text_for_unassociated_photo_creates_entry(self, tmp_path):
        client, config_path = make_client(tmp_path)

        response = client.post("/items/1/text", json={"text": "caption for b"})

        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}
        assert "caption for b" in config_path.read_text()

        # reflected back when viewing the photo again
        page = client.get("/items/1").get_data(as_text=True)
        assert "caption for b" in page

    def test_saving_edit_to_existing_text_updates_in_place(self, tmp_path):
        client, config_path = make_client(tmp_path)

        response = client.post("/items/0/text", json={"text": "updated caption for a"})

        assert response.status_code == 200
        content = config_path.read_text()
        assert "updated caption for a" in content
        assert "existing caption for a" not in content

    def test_saving_empty_text_is_allowed(self, tmp_path):
        client, config_path = make_client(tmp_path)

        response = client.post("/items/0/text", json={"text": ""})

        assert response.status_code == 200
        # semantic check (YAML quoting style for an empty scalar can
        # legitimately vary) rather than a raw string match
        reloaded = load_config(config_path)
        assert reloaded.text_labels[0]["text"] == ""

    def test_missing_text_field_is_bad_request(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.post("/items/0/text", json={"nope": "value"})
        assert response.status_code == 400

    def test_non_json_body_is_bad_request(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.post("/items/0/text", data="not json")
        assert response.status_code == 400

    def test_out_of_range_index_is_404(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.post("/items/99/text", json={"text": "x"})
        assert response.status_code == 404


class TestPhotoDirectoryCaching:
    def test_multiple_routes_share_one_photo_directory_scan(self, tmp_path, monkeypatch):
        original = data_module.collect_photos
        calls = {"count": 0}

        def wrapper(*args, **kwargs):
            calls["count"] += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(data_module, "collect_photos", wrapper)

        client, _ = make_client(tmp_path)
        client.get("/items/0")
        client.get("/items/0/image")
        client.get("/items/1")

        assert calls["count"] == 1


class TestTitleNavigation:
    def test_view_title_shows_content_without_photo_frame(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        response = client.get("/items/1")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "Existing Title" in body
        assert 'id="delete-title-button"' in body
        assert "<img" not in body

    def test_view_photo_around_title_offers_add_title_not_delete(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        body = client.get("/items/0").get_data(as_text=True)
        assert 'id="add-title-button"' in body
        assert 'id="delete-title-button"' not in body

    def test_view_title_does_not_offer_add_title(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        body = client.get("/items/1").get_data(as_text=True)
        assert 'id="add-title-button"' not in body


class TestSaveTitle:
    def test_saving_title_text_updates_in_place(self, tmp_path):
        client, config_path = make_client_with_title(tmp_path)

        response = client.post("/items/1/title", json={"text": "New Title"})

        assert response.status_code == 200
        content = config_path.read_text()
        assert "New Title" in content
        assert "Existing Title" not in content

    def test_saving_title_on_photo_index_is_bad_request(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        response = client.post("/items/0/title", json={"text": "x"})
        assert response.status_code == 400

    def test_saving_text_on_title_index_is_bad_request(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        response = client.post("/items/1/text", json={"text": "x"})
        assert response.status_code == 400


class TestAddTitle:
    def test_add_title_before_photo_creates_entry_at_photo_timestamp(self, tmp_path):
        client, config_path = make_client_with_title(tmp_path)

        response = client.post("/items/0/add-title")

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["index"] == 0  # the new title takes the photo's old slot

        body = client.get("/items/0").get_data(as_text=True)
        assert 'id="delete-title-button"' in body

        reloaded = load_config(config_path)
        title_entries = [entry for entry in reloaded.text_labels if "title" in entry]
        assert any(entry["title"] == "" for entry in title_entries)

    def test_add_title_on_title_index_is_bad_request(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        response = client.post("/items/1/add-title")
        assert response.status_code == 400

    def test_add_title_on_out_of_range_index_is_404(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        response = client.post("/items/99/add-title")
        assert response.status_code == 404


class TestDeleteTitle:
    def test_delete_title_navigates_to_following_photo(self, tmp_path):
        client, config_path = make_client_with_title(tmp_path)

        response = client.post("/items/1/delete-title")

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["index"] == 1  # b.jpg now occupies the title's old slot

        content = config_path.read_text()
        assert "Existing Title" not in content

        body = client.get("/items/1").get_data(as_text=True)
        assert "b.jpg" in body

    def test_delete_title_that_was_last_navigates_to_previous_item(self, tmp_path):
        client, config_path = make_client_with_trailing_title(tmp_path)
        # merged order: [a.jpg(0), b.jpg(1), title(2) - trailing, no following item]

        response = client.post("/items/2/delete-title")

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["index"] == 1  # clamped to the new last item (b.jpg)

        assert "Trailing Title" not in config_path.read_text()
        body = client.get("/items/1").get_data(as_text=True)
        assert "b.jpg" in body

    def test_delete_title_on_photo_index_is_bad_request(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        response = client.post("/items/0/delete-title")
        assert response.status_code == 400

    def test_delete_title_on_out_of_range_index_is_404(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        response = client.post("/items/99/delete-title")
        assert response.status_code == 404


class TestGeoButtonMarkup:
    def test_photo_with_gps_shows_enabled_button(self, tmp_path):
        client, _ = make_client_with_gps(tmp_path)  # a.jpg (index 0) has GPS
        body = client.get("/items/0").get_data(as_text=True)

        assert 'id="geo-button"' in body
        button_tag = body.split('id="geo-button"')[1].split(">")[0]
        assert "disabled" not in button_tag

    def test_photo_without_gps_shows_disabled_button_with_reason(self, tmp_path):
        client, _ = make_client_with_gps(tmp_path)  # b.jpg (index 1) has no GPS
        body = client.get("/items/1").get_data(as_text=True)

        button_tag = body.split('id="geo-button"')[1].split(">")[0]
        assert "disabled" in button_tag
        assert "title=" in button_tag

    def test_title_item_does_not_show_button(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        body = client.get("/items/1").get_data(as_text=True)  # the title item

        assert 'id="geo-button"' not in body


class TestReverseGeocode:
    def test_photo_with_gps_returns_resolved_place_name(self, tmp_path, monkeypatch):
        client, _ = make_client_with_gps(tmp_path)  # a.jpg (index 0) has GPS

        def fake_reverse_geocode(lat, lon, accept_language=""):
            return {"name": "St. Michaelis Church"}

        monkeypatch.setattr(geocoding_module, "reverse_geocode", fake_reverse_geocode)

        response = client.post("/items/0/reverse-geocode")

        assert response.status_code == 200
        assert response.get_json() == {"status": "ok", "text": "St. Michaelis Church"}

    def test_forwards_accept_language_header(self, tmp_path, monkeypatch):
        client, _ = make_client_with_gps(tmp_path)
        captured = {}

        def fake_reverse_geocode(lat, lon, accept_language=""):
            captured["accept_language"] = accept_language
            return {"name": "Plaza España"}

        monkeypatch.setattr(geocoding_module, "reverse_geocode", fake_reverse_geocode)

        client.post("/items/0/reverse-geocode", headers={"Accept-Language": "es-ES"})

        assert captured["accept_language"] == "es-ES"

    def test_photo_without_gps_is_bad_request(self, tmp_path):
        client, _ = make_client_with_gps(tmp_path)  # b.jpg (index 1) has no GPS
        response = client.post("/items/1/reverse-geocode")
        assert response.status_code == 400

    def test_title_index_is_bad_request(self, tmp_path):
        client, _ = make_client_with_title(tmp_path)
        response = client.post("/items/1/reverse-geocode")
        assert response.status_code == 400

    def test_out_of_range_index_is_404(self, tmp_path):
        client, _ = make_client_with_gps(tmp_path)
        response = client.post("/items/99/reverse-geocode")
        assert response.status_code == 404

    def test_service_error_is_non_2xx_with_error_status(self, tmp_path, monkeypatch):
        client, _ = make_client_with_gps(tmp_path)

        def failing_reverse_geocode(lat, lon, accept_language=""):
            raise geocoding_module.GeocodingError("boom")

        monkeypatch.setattr(geocoding_module, "reverse_geocode", failing_reverse_geocode)

        response = client.post("/items/0/reverse-geocode")

        assert response.status_code >= 400
        payload = response.get_json()
        assert payload["status"] == "error"

    def test_no_resolvable_location_is_non_2xx_with_error_status(self, tmp_path, monkeypatch):
        client, _ = make_client_with_gps(tmp_path)

        def empty_reverse_geocode(lat, lon, accept_language=""):
            return {}

        monkeypatch.setattr(geocoding_module, "reverse_geocode", empty_reverse_geocode)

        response = client.post("/items/0/reverse-geocode")

        assert response.status_code >= 400
        payload = response.get_json()
        assert payload["status"] == "error"
