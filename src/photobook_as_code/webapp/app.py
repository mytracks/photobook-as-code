"""
Flask application for the text_labels web editor.
"""

import io
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, url_for
from PIL import Image

from . import yaml_store
from .data import load_editor_data

MAX_IMAGE_DIMENSION = 1600
JPEG_QUALITY = 85


def create_app(config_path: Path) -> Flask:
    """Build the Flask app bound to a single photobook configuration file."""
    app = Flask(__name__)
    app.config["PHOTOBOOK_CONFIG_PATH"] = Path(config_path)

    def _load_data_or_404(index: int):
        data = load_editor_data(app.config["PHOTOBOOK_CONFIG_PATH"])
        if index < 0 or index >= data.count:
            abort(404)
        return data

    @app.get("/")
    def index():
        return redirect(url_for("view_photo", index=0))

    @app.get("/photos/<int:index>")
    def view_photo(index: int):
        data = _load_data_or_404(index)
        photo = data.photo_at(index)
        return render_template(
            "editor.html",
            index=index,
            total=data.count,
            filename=photo.filename,
            text=data.text_for(index),
            has_prev=index > 0,
            has_next=index < data.count - 1,
        )

    @app.get("/photos/<int:index>/image")
    def photo_image(index: int):
        data = _load_data_or_404(index)
        photo = data.photo_at(index)

        with Image.open(photo.path) as img:
            img = img.convert("RGB")
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=JPEG_QUALITY)
            buf.seek(0)

        return send_file(buf, mimetype="image/jpeg")

    @app.post("/photos/<int:index>/text")
    def save_text(index: int):
        data = _load_data_or_404(index)

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

    return app
