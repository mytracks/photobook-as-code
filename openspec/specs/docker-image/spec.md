# docker-image Specification

## Purpose

Lets a user run the photobook renderer and the text-labels web editor without installing Python, system fonts, or any dependency locally, by pulling and running a single published Docker image.

## Requirements

### Requirement: Installed package includes runtime data files
A non-editable install of the package (`pip install .` or from a built wheel/sdist) SHALL include the built-in theme definitions, the web editor's HTML template, and its static assets, so the installed package behaves identically to an editable/source checkout.

#### Scenario: Built-in theme available after a standard install
- **WHEN** the package is installed via `pip install .` (not `-e`) into a clean environment and `photobook` is run against a config using a built-in theme (e.g. `clean`)
- **THEN** the theme loads successfully and the photobook is generated, with no "theme not found" error

#### Scenario: Web editor UI available after a standard install
- **WHEN** the package is installed via `pip install .` (not `-e`) into a clean environment and `photobook-edit-labels` is started
- **THEN** requesting `/items/0` returns the rendered editor page (template found), and its static assets (`editor.js`, `style.css`) are served successfully

### Requirement: Docker image runs the renderer
The Docker image SHALL run the `photobook` command directly, rendering a photobook from a mounted YAML configuration and mounted photo folder(s) to a mounted output location, then exit.

#### Scenario: Render a photobook via docker run
- **WHEN** a user runs the image with a config file, photo folder, and output directory bind-mounted, passing `photobook --config <mounted-config-path>`
- **THEN** the container generates the configured PDF/PNG/JPG output into the mounted output location and exits with status 0, matching what running `photobook` locally against the same inputs would produce

### Requirement: Docker image runs the web editor
The Docker image SHALL run the `photobook-edit-labels` command directly, serving the web editor on a host/port reachable from outside the container.

#### Scenario: Start the web editor via docker run
- **WHEN** a user runs the image with a config file bind-mounted and a container port published to the host, passing `photobook-edit-labels --config <mounted-config-path> --host 0.0.0.0 --port <port>`
- **THEN** the editor is reachable at `http://localhost:<published-port>/` from the host, and text/title edits made through it are saved back into the mounted config file on the host

### Requirement: Docker image includes required fonts
The Docker image SHALL include the font files each built-in theme depends on, so rendering a photobook with any built-in theme succeeds with no additional host or container setup.

#### Scenario: Render with each built-in theme
- **WHEN** `photobook` is run inside the container against configs selecting each of the built-in themes (`clean`, `classic`, `modern`)
- **THEN** each render succeeds with no missing-font error

### Requirement: Docker image builds and runs on multiple architectures
The Docker image SHALL build as a multi-arch manifest supporting both `linux/amd64` and `linux/arm64`, and SHALL run correctly on each, so that once published `docker run` succeeds on both Intel/AMD hosts and ARM hosts (e.g. Apple Silicon, Raspberry Pi) without the user selecting a platform-specific tag. Publishing the built image to a registry is out of scope for this requirement (tracked separately).

#### Scenario: Build for both target platforms
- **WHEN** `docker buildx build --platform linux/amd64,linux/arm64` is run against `docker/Dockerfile`
- **THEN** the build completes successfully for both platforms

#### Scenario: Image runs correctly on each built platform
- **WHEN** the built image is run with `--platform linux/amd64` and separately with `--platform linux/arm64`
- **THEN** both the `photobook` and `photobook-edit-labels` commands work correctly on each platform
