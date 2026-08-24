"""
Flask application for the text_labels web editor.
"""

import io
from pathlib import Path
from typing import Optional

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, url_for
from PIL import Image

from . import yaml_store
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

        if data.is_title(index):
            return render_template(
                "editor.html",
                index=index,
                total=data.count,
                is_title=True,
                title_text=data.title_text_for(index),
                has_prev=index > 0,
                has_next=index < data.count - 1,
            )

        photo = data.photo_at(index)
        return render_template(
            "editor.html",
            index=index,
            total=data.count,
            is_title=False,
            filename=photo.filename,
            text=data.text_for(index),
            has_prev=index > 0,
            has_next=index < data.count - 1,
            date_display=data.display_date(index),
            is_new_day=data.is_new_day(index),
            photo_width=photo.width,
            photo_height=photo.height,
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
