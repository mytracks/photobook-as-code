# Photobook as Code

Generate print-ready photobook layouts from a YAML configuration — no Python,
system fonts, or dependencies to install. Pull the image and run one of two
commands directly with `docker run`.

- `photobook` — renders a photobook (PDF/PNG/JPG) from a config and photo
  folder(s), then exits.
- `photobook-edit-labels` — serves a small local web UI for writing the
  photo captions (`text_labels`) that `photobook` renders, saving edits back
  into the same config file.

Full project docs, source, and issue tracker:
[github.com/mytracks/photobook-as-code](https://github.com/mytracks/photobook-as-code).
Licensed under the [MIT License](https://github.com/mytracks/photobook-as-code/blob/main/LICENSE).

## Supported tags

- `latest` — most recent release
- `0.1.0` — pinned version

Each tag is a multi-arch manifest supporting `linux/amd64` and `linux/arm64`
(e.g. Apple Silicon, Raspberry Pi) — `docker pull`/`docker run` select the
right variant automatically, no platform-specific tag needed.

```bash
docker pull mytracks/photobook-as-code
```

## Volume-mount convention

The image has no opinion on host paths — `photo_folders` and `output` in
your YAML config decide everything. The examples below use the same mount
points as this project's `example-config.yaml` and devcontainer, so an
existing config works unmodified:

| Host                | Container       | Purpose                          |
|----------------------|-----------------|-----------------------------------|
| `~/Pictures`         | `/mnt/pictures` | Source photos (read-only)         |
| `~/Downloads`        | `/mnt/downloads`| Rendered output                   |
| directory holding your config | `/config` | The YAML config file to read/write |

Mount the **directory** containing your config file at `/config` (not the
file itself) — both commands need to atomically rewrite the config in place,
which requires the config's parent directory to be a real mount, not a
single bind-mounted file.

Any other mount layout works equally well as long as your YAML config's
`photo_folders` / `output` paths match the container-side paths you chose.

## Render a photobook

```bash
docker run --rm \
  -v ~/Pictures:/mnt/pictures:ro \
  -v ~/Downloads:/mnt/downloads \
  -v "$(pwd)":/config \
  mytracks/photobook-as-code \
  photobook --config /config/my-photobook.yaml
```

The container exits once rendering finishes; the output PDF/PNG/JPG appears
under `~/Downloads` (or wherever your config's `output.directory` points).

## Edit captions with the web editor

```bash
docker run --rm \
  -v ~/Pictures:/mnt/pictures:ro \
  -v "$(pwd)":/config \
  -p 5000:5000 \
  mytracks/photobook-as-code \
  photobook-edit-labels --config /config/my-photobook.yaml --host 0.0.0.0 --port 5000
```

Then open `http://localhost:5000/` in a browser. Edits are written straight
back into the mounted config file as you navigate between photos.

**This is a local/trusted-network tool, not a hardened web service.** It
runs Flask's built-in development server with no authentication. Don't
publish its port beyond your own machine or trusted network.

## All built-in themes included

The image ships the fonts (`fonts-dejavu-extra`) every built-in theme
(`clean`, `classic`, `modern`) depends on, so rendering with any of them
works out of the box — no extra setup.
