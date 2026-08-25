## Context

See `proposal.md` - Why/What Changes for motivation. Relevant constraints discovered while investigating:

- `renderer.py` hardcodes font paths as `/usr/share/fonts/truetype/dejavu/{family}(-Bold|-Oblique|-BoldOblique).ttf`. That exact layout is Debian's `fonts-dejavu-extra` package (already what `.devcontainer/devcontainer.json` installs) — it doesn't exist on Alpine.
- `pikepdf` wraps the `qpdf` C library; prebuilt wheels are far more reliably available for glibc/manylinux targets than musllinux/Alpine.
- `pyproject.toml` currently declares no `package-data`, so `pip install .` drops `themes/*.yaml`, `webapp/templates/editor.html`, and `webapp/static/*` (verified by a real install into a clean venv).
- `example-config.yaml` and `.devcontainer/devcontainer.json` already establish a host-mount convention: `~/Pictures` → `/mnt/pictures`, `~/Downloads` → `/mnt/downloads`.
- Both `photobook` and `photobook-edit-labels` are plain `console_scripts` entry points (`pyproject.toml`) — no wrapper process or shared server needed to run either.

## Goals / Non-Goals

**Goals:**
- One image, two independently runnable commands, no custom entrypoint logic.
- Small image (slim base, multi-stage, no leftover build/apt caches).
- Existing configs (e.g. `example-config.yaml`) work unmodified when mounted at the documented paths.
- amd64 + arm64 support from the first published tag.

**Non-Goals:**
- No production-hardening of the Flask dev server (auth, WSGI server, TLS) — it remains what the project's own docs already describe: a small local/trusted-network tool.
- No CI/CD publish pipeline in this change (explicitly deferred by the user).
- No fix to unrelated pre-existing renderer behavior outside the packaging bug this change depends on (see Risks).

## Decisions

**Base image: `python:3.12-slim` (Debian), not Alpine.**
Alternative considered: Alpine, for a smaller base. Rejected because the renderer's font paths and `fonts-dejavu-extra` package layout are Debian-specific, and `pikepdf`/`Pillow` wheel coverage for musllinux is less reliable. `python:*-slim` gives most of Alpine's size benefit without fighting either constraint.

**Multi-stage build.**
A builder stage installs the package (and its pip-installable deps) into an isolated location; the final stage copies only the installed package plus `apt-get install --no-install-recommends fonts-dejavu-extra`, with apt lists and pip cache removed. Keeps the shipped image free of compilers/build headers even though today's dependencies are pure-wheel installs (guards against a future dependency that isn't).

**Fix the packaging gap in `pyproject.toml` directly (not worked around in the Dockerfile).**
Alternative considered: `COPY` the source tree into the image and `pip install -e .` so the files are present without touching packaging metadata. Rejected (per explicit decision) because the missing `package-data` is a real bug independent of Docker — every non-editable install is affected — and fixing it in the Dockerfile only would leave PyPI/non-Docker installs broken.

**No custom entrypoint/dispatcher script.**
Both commands are already installed console scripts; the image needs no `ENTRYPOINT` beyond the default, and users simply run `docker run <image> photobook --config ...` or `docker run <image> photobook-edit-labels --config ... --host 0.0.0.0`. Alternative considered: an `entrypoint.sh` that inspects `$1` to decide render-vs-serve. Rejected as unnecessary indirection — it would only reimplement what `docker run <image> <command>` already does natively.

**Document, don't hardcode, the `/mnt/pictures` / `/mnt/downloads` / `/config` mount convention.**
The Dockerfile itself has no opinion on mount paths (photo folders and output paths come entirely from the mounted YAML config, per its `photo_folders`/`output` keys). `docker/README.md` recommends mounting at the same paths `example-config.yaml` and the devcontainer already use, purely so existing configs need no path edits. Any other mount path works equally well as long as the YAML config matches it.

**Multi-arch via `docker buildx build --platform linux/amd64,linux/arm64`, run manually. Publishing (`--push` to Docker Hub) is deferred to a later change.**
This change delivers and verifies the buildable, multi-arch image (built and functionally smoke-tested locally on both platforms). No GitHub Actions workflow in this change (explicit decision), and no `docker push` either — actually publishing `mytracks/photobook-as-code` to Docker Hub, with its own verification (pull on both tags, confirm on an arm64 host), is out of scope here and left to a follow-up change. The `docker/README.md` / task notes should still record the exact buildx command so that later push is reproducible.

**Docker artifacts live in `docker/`; build context stays the repo root.**
`docker/Dockerfile` and `docker/README.md` are the only new files outside `pyproject.toml`. Because the image needs `pyproject.toml` and `src/`, the build is invoked as `docker build -f docker/Dockerfile .` (context = repo root), not `docker build docker/`. Verified empirically: with the Dockerfile at `docker/Dockerfile` and context `.`, BuildKit only honors a Dockerfile-adjacent `docker/Dockerfile.dockerignore` (not a bare `docker/.dockerignore`, nor `docker build docker/`'s context root) — so that's where the ignore rules for `.git`, generated `*.pdf`/`output/`, and other repo clutter (e.g. the 69MB `my-photobook.pdf` sample at repo root) live.

## Risks / Trade-offs

- [Risk] Flask's built-in dev server (`photobook-edit-labels`) is single-threaded and has no auth → [Mitigation] `docker/README.md` states explicitly this is a local/trusted-network tool, matching the main README's existing framing; not exposed publicly by default (user must explicitly publish the port).
- [Risk] `pikepdf`/`Pillow` might lack a prebuilt wheel for one of the two target platforms at build time → [Mitigation] `python:*-slim` (glibc/manylinux) chosen specifically to maximize wheel coverage; verified `docker buildx build --platform linux/amd64,linux/arm64` succeeds and both platforms run correctly (native arm64, QEMU-emulated amd64) before the (deferred, later-change) first publish.
- [Risk] Users with configs pointing at mount paths other than `/mnt/pictures`/`/mnt/downloads`/`/config` will need to adjust either their config or their `-v` flags → [Mitigation] README states this is a recommendation, not a requirement; any consistent mount path works.
- [Risk, pre-existing, out of scope] `renderer.py` builds italic font filenames as `{family}-Oblique.ttf` for every theme, but DejaVu's serif italic file is actually named `DejaVuSerif-Italic.ttf`. This would affect the `classic` theme's italic text identically whether run locally or in the container — it's not introduced or fixed by this change, and fixing it is out of scope here.
- [Risk] Repo root contains large/irrelevant files (a 69MB sample PDF, example YAMLs) that would bloat the build context if not excluded → [Mitigation] `.dockerignore` scoped to the chosen build context.

## Migration Plan

Purely additive — no existing users or deployments depend on a Docker image today, so there's nothing to migrate and no rollback complexity beyond not publishing (or deleting) a bad tag.

Rollout steps for this change: build and smoke-test both commands locally (`docker build` → `docker run ... photobook ...` and `docker run ... photobook-edit-labels ...` against the repo's example configs) → `docker buildx build --platform linux/amd64,linux/arm64`, verified functionally on both platforms.

Publishing — manual `docker push` to `mytracks/photobook-as-code` with a version tag (matching `pyproject.toml`'s `0.1.0`) and `latest`, and confirming the published tags pull and run correctly (including on an arm64 host) — is deferred to a later change.

## Open Questions

- Exact base image tag (e.g. `python:3.12-slim` vs `3.13-slim`) — an implementation-time pick, doesn't change the spec or approach.
- Whether to also ship a `docker-compose.yml` alongside the Dockerfile for convenience — nice-to-have, not required by any spec requirement here; can be added later without touching the specs.
- Tagging scheme beyond `latest` + the current version (e.g. whether to tag `0.1`, `0`) — cosmetic, deferrable.
