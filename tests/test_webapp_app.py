"""
Integration tests for the web editor's Flask routes.
"""

from pathlib import Path

from PIL import Image

from photobook_as_code.config import load_config
from photobook_as_code.webapp.app import create_app


def _make_photos_dir(tmp_path: Path) -> Path:
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    Image.new("RGB", (2000, 1500), color="white").save(photos_dir / "a.jpg")
    Image.new("RGB", (2000, 1500), color="white").save(photos_dir / "b.jpg")
    return photos_dir


def _write_config(tmp_path: Path, photos_dir: Path) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"photos: {photos_dir}\n"
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


def make_client(tmp_path):
    photos_dir = _make_photos_dir(tmp_path)
    config_path = _write_config(tmp_path, photos_dir)
    app = create_app(config_path)
    app.config["TESTING"] = True
    return app.test_client(), config_path


class TestNavigation:
    def test_root_redirects_to_first_photo(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.get("/")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/photos/0")

    def test_view_first_photo_shows_existing_text(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.get("/photos/0")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "a.jpg" in body
        assert "existing caption for a" in body
        assert 'id="next-link"' in body

    def test_view_second_photo_shows_empty_text(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.get("/photos/1")
        assert response.status_code == 200
        assert "b.jpg" in response.get_data(as_text=True)

    def test_out_of_range_index_is_404(self, tmp_path):
        client, _ = make_client(tmp_path)
        assert client.get("/photos/99").status_code == 404
        assert client.get("/photos/-1").status_code == 404


class TestPhotoImage:
    def test_image_is_served_as_jpeg(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.get("/photos/0/image")
        assert response.status_code == 200
        assert response.mimetype == "image/jpeg"

    def test_image_out_of_range_is_404(self, tmp_path):
        client, _ = make_client(tmp_path)
        assert client.get("/photos/99/image").status_code == 404


class TestSaveText:
    def test_saving_new_text_for_unassociated_photo_creates_entry(self, tmp_path):
        client, config_path = make_client(tmp_path)

        response = client.post("/photos/1/text", json={"text": "caption for b"})

        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}
        assert "caption for b" in config_path.read_text()

        # reflected back when viewing the photo again
        page = client.get("/photos/1").get_data(as_text=True)
        assert "caption for b" in page

    def test_saving_edit_to_existing_text_updates_in_place(self, tmp_path):
        client, config_path = make_client(tmp_path)

        response = client.post("/photos/0/text", json={"text": "updated caption for a"})

        assert response.status_code == 200
        content = config_path.read_text()
        assert "updated caption for a" in content
        assert "existing caption for a" not in content

    def test_saving_empty_text_is_allowed(self, tmp_path):
        client, config_path = make_client(tmp_path)

        response = client.post("/photos/0/text", json={"text": ""})

        assert response.status_code == 200
        # semantic check (YAML quoting style for an empty scalar can
        # legitimately vary) rather than a raw string match
        reloaded = load_config(config_path)
        assert reloaded.text_labels[0]["text"] == ""

    def test_missing_text_field_is_bad_request(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.post("/photos/0/text", json={"nope": "value"})
        assert response.status_code == 400

    def test_non_json_body_is_bad_request(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.post("/photos/0/text", data="not json")
        assert response.status_code == 400

    def test_out_of_range_index_is_404(self, tmp_path):
        client, _ = make_client(tmp_path)
        response = client.post("/photos/99/text", json={"text": "x"})
        assert response.status_code == 404
