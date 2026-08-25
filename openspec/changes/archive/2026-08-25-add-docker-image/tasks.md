## 1. Fix package-data (pyproject.toml)

- [x] 1.1 Add `package-data`/`include-package-data` config to `pyproject.toml` so `photobook_as_code/themes/*.yaml`, `photobook_as_code/webapp/templates/*`, and `photobook_as_code/webapp/static/*` are included in a build/install (add a `MANIFEST.in` too if `setuptools` needs it for sdist inclusion).
- [x] 1.2 Verify: install into a clean venv via `pip install .` (not `-e`) and confirm `themes/*.yaml`, `webapp/templates/editor.html`, `webapp/static/editor.js`, `webapp/static/style.css` exist under the installed `site-packages/photobook_as_code/` tree.
- [x] 1.3 Verify: from that clean-venv install, run `photobook --config <minimal test config using a built-in theme>` and confirm it succeeds (no `ThemeError`).
- [x] 1.4 Verify: from that clean-venv install, run `photobook-edit-labels --config <same test config>` and confirm `GET /items/0` returns 200 (template found) and `GET` for `editor.js`/`style.css` return 200.

## 2. Dockerfile

- [x] 2.1 Create `docker/Dockerfile`: multi-stage build — a builder stage on `python:3.12-slim` that installs the package and its dependencies, and a final stage on `python:3.12-slim` that `apt-get install --no-install-recommends fonts-dejavu-extra`, copies the installed package from the builder, and cleans up apt lists/pip cache.
- [x] 2.2 Add `docker/.dockerignore` (matching whatever build context `docker build -f docker/Dockerfile .` uses) excluding `.git`, `*.pdf`, `output/`, `__pycache__`, `.venv`, `openspec/`, and other non-runtime repo content.
- [x] 2.3 Verify: `docker build -f docker/Dockerfile -t photobook-as-code:local .` completes successfully.
- [x] 2.4 Verify: `docker run --rm photobook-as-code:local photobook --help` and `docker run --rm photobook-as-code:local photobook-edit-labels --help` both print their CLI help with no import/missing-file errors.

## 3. Renderer and web editor smoke tests (single-arch image)

- [x] 3.1 Verify (renderer): run `photobook-as-code:local` with a config, a photo folder, and an output directory bind-mounted, passing `photobook --config <mounted-config>`; confirm the configured PDF/PNG/JPG appears in the mounted output directory on the host and the container exits 0.
- [x] 3.2 Verify (renderer, fonts): repeat 3.1 once per built-in theme (`clean`, `classic`, `modern`) and confirm each succeeds with no missing-font error.
- [x] 3.3 Verify (web editor): run `photobook-as-code:local` with a config bind-mounted and a port published, passing `photobook-edit-labels --config <mounted-config> --host 0.0.0.0 --port <port>`; confirm `http://localhost:<port>/` loads in a browser/curl.
- [x] 3.4 Verify (web editor, persistence): from 3.3, edit a caption through the UI (or via its `POST /items/<n>/text` endpoint) and confirm the change is written back into the config file on the host.

## 4. Multi-arch build

- [x] 4.1 Confirm a `docker buildx` builder supporting `linux/amd64` and `linux/arm64` is available (`docker buildx inspect --bootstrap`), creating one if needed.
- [x] 4.2 Verify: `docker buildx build --platform linux/amd64,linux/arm64 -f docker/Dockerfile -t mytracks/photobook-as-code:0.1.0 -t mytracks/photobook-as-code:latest .` completes successfully for both platforms.

Pushing the built multi-arch manifest to Docker Hub is out of scope for this change — deferred to a later change.

## 5. Docker Hub README

- [x] 5.1 Write `docker/README.md` for the Docker Hub "Overview" tab: what the image does, supported tags, `docker pull mytracks/photobook-as-code` quick reference, `docker run` examples for both the renderer and the web editor, the recommended volume-mount convention (`/mnt/pictures`, `/mnt/downloads`, `/config` — matching `example-config.yaml`), an explicit note that the web editor is a local/trusted-network tool (no auth), and links back to the GitHub repo and license.
- [x] 5.2 Verify: run every `docker run`/`docker pull` example in `docker/README.md` verbatim against the locally built image and confirm each behaves as documented.

## 6. End-to-end verification against the spec

- [x] 6.1 Verify each scenario in `openspec/changes/add-docker-image/specs/docker-image/spec.md` passes: standard install includes theme/template/static files; `docker run … photobook …` renders; `docker run … photobook-edit-labels …` serves and persists edits; all built-in themes render (fonts present); `docker buildx build --platform linux/amd64,linux/arm64` succeeds; the built image runs correctly on both platforms (verified locally: native arm64 plus QEMU-emulated amd64, including a full render).
