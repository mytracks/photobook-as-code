## Why

Right now, using this tool requires a local Python environment, the exact system font package (`fonts-dejavu-extra`) the renderer's hardcoded font paths depend on, and (for the web editor) manually running a Flask dev server. A Docker image lets a user run either the renderer or the web editor with a single `docker run`, with no Python/font setup on the host. While verifying this was feasible, we also confirmed a real, pre-existing bug: a plain `pip install .` silently drops `themes/*.yaml`, `webapp/templates/editor.html`, and `webapp/static/*` because `pyproject.toml` declares no `package-data`. This breaks every non-editable install, not just the Docker image, and must be fixed for the image to work at all.

## What Changes

- Fix `pyproject.toml` packaging so a standard (non-editable) install includes the built-in themes, the web editor's Jinja template, and its static assets.
- Add a `docker/` folder containing a multi-stage `Dockerfile` (light `python:*-slim` base + `fonts-dejavu-extra`) that installs the package and exposes both `photobook` (renderer, batch) and `photobook-edit-labels` (web editor, long-running) as directly runnable commands — no custom entrypoint dispatch needed.
- Build the image for both `amd64` and `arm64` (via `docker buildx`).
- Add `docker/README.md` written for the Docker Hub "Overview" page: pull command (`mytracks/photobook-as-code`), quick-start `docker run` examples for both modes, and the recommended volume-mount convention (`/mnt/pictures`, `/mnt/downloads`, `/config`) that already matches this repo's `example-config.yaml` and `.devcontainer/devcontainer.json`.
- No GitHub Actions publish workflow in this change. Pushing the built image to Docker Hub is deferred entirely to a later change — this change delivers and verifies the buildable, multi-arch image only.

## Capabilities

### New Capabilities
- `docker-image`: Running the renderer and the web editor from a prebuilt Docker image, including the packaging fix that makes a non-editable install (which the image relies on) actually include the tool's data files.

### Modified Capabilities
(none — no existing capability's requirements change)

## Impact

- **Affected code**: `pyproject.toml` (package-data declaration); new `docker/Dockerfile`, `docker/README.md`, `docker/.dockerignore`.
- **Dependencies**: `python:*-slim` base image, Debian `fonts-dejavu-extra` package (already required at runtime by `renderer.py`'s hardcoded font paths).
- **Systems**: Docker Hub (`mytracks/photobook-as-code`), built manually via `docker buildx` for `amd64`+`arm64`.
- **Not affected**: application source code/behavior of the renderer or web editor themselves — only how they're packaged and distributed.
