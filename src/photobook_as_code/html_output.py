"""
HTML slideshow generation: a single self-contained, endlessly-looping HTML
file with one slide per page item, referencing photos by relative path.
"""

import base64
import html as html_lib
import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple, Union
from urllib.parse import quote

from .photos import PhotoMetadata
from .renderer import font_variant_paths, hex_to_rgb
from .text_labels import TextLabel, TitleLabel, parse_markdown_text
from .themes import Theme

logger = logging.getLogger(__name__)

PageItem = Union[PhotoMetadata, TitleLabel]

DEFAULT_INTERVAL_SECONDS = 5.0


class HtmlOutputError(Exception):
    """Raised when HTML slideshow generation fails."""
    pass


def _relative_href(photo_path: Path, base_dir: Path) -> str:
    """
    A URL-safe relative path from base_dir to photo_path: POSIX-separated
    (so it resolves the same way on any OS the browser runs on) and
    percent-encoded (so spaces/non-ASCII names resolve correctly as a URL,
    both under file:// and http(s)). '/' is left unescaped so directory
    structure, including '../' traversal into a sibling photo folder, is
    preserved.
    """
    rel = os.path.relpath(photo_path, base_dir)
    rel_posix = Path(rel).as_posix()
    return quote(rel_posix, safe='/')


def _render_markdown_html(text: str) -> str:
    """
    Render a caption/title's Markdown into the equivalent HTML markup, using
    the same parsed structure (`parse_markdown_text`) the PDF/image renderer
    uses - bold/italic segments become <strong>/<em>, and a heading line's
    font_size_multiplier becomes an inline font-size. Rendering happens once,
    server-side, at generation time - the generated page ships no markdown
    parser of its own.
    """
    parsed_lines = parse_markdown_text(text)
    if not parsed_lines:
        return ""

    rendered_lines = []
    for segments, _heading_level in parsed_lines:
        if not any(segment.text for segment in segments):
            rendered_lines.append('<div class="ps-line">&nbsp;</div>')
            continue

        parts = []
        for segment in segments:
            escaped = html_lib.escape(segment.text)
            if segment.bold and segment.italic:
                escaped = f"<strong><em>{escaped}</em></strong>"
            elif segment.bold:
                escaped = f"<strong>{escaped}</strong>"
            elif segment.italic:
                escaped = f"<em>{escaped}</em>"
            parts.append(escaped)

        multiplier = segments[0].font_size_multiplier
        style_attr = f' style="font-size:{multiplier}em"' if multiplier != 1.0 else ""
        rendered_lines.append(f'<div class="ps-line"{style_attr}>{"".join(parts)}</div>')

    return "".join(rendered_lines)


def _embed_font_face_rules(font_family: str, css_family_name: str) -> str:
    """
    Base64-embed a font family's regular/bold/italic/bold-italic variants as
    inline @font-face rules, using the same file-resolution logic the PDF/PNG
    renderer uses (`font_variant_paths`), so the html slideshow doesn't
    depend on that font being installed on the viewer's system. Returns ""
    if any variant file can't be found, so the caller's CSS font stack falls
    back to its generic keyword instead - mirroring the PIL renderer's own
    fallback-to-default-font behavior.
    """
    regular, bold, italic, bold_italic = font_variant_paths(font_family)
    variants = [
        (regular, "normal", "normal"),
        (bold, "bold", "normal"),
        (italic, "normal", "italic"),
        (bold_italic, "bold", "italic"),
    ]

    if not all(path.exists() for path, _, _ in variants):
        logger.warning(
            f"Could not find all font files for '{font_family}' under "
            f"{regular.parent}; html slideshow will fall back to a generic font"
        )
        return ""

    rules = []
    for path, weight, style in variants:
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            f"@font-face{{font-family:'{css_family_name}';font-weight:{weight};"
            f"font-style:{style};src:url(data:font/ttf;base64,{data}) format('truetype');}}"
        )
    return "".join(rules)


def _resolve_theme_fonts(theme: Theme) -> Tuple[str, str, str]:
    """
    Embed each distinct font family the theme's text/title styles name at
    most once - the text and title styles commonly share the same family
    (every built-in theme except 'classic' does), and embedding it twice
    would needlessly double the file's size for no visual benefit.

    Returns:
        (font_face_css, caption_font_family_css_value, title_font_family_css_value)
        where the two font-family values are ready to drop straight into a
        CSS `font-family` declaration (a quoted embedded name plus a
        'sans-serif' fallback, or just 'sans-serif' if embedding failed).
    """
    embedded_css_name: dict = {}  # font_family -> css name, or None if embedding failed
    face_rules = []

    def resolve(font_family: str) -> str:
        if font_family not in embedded_css_name:
            css_name = f"PBFont{len(embedded_css_name)}"
            rules = _embed_font_face_rules(font_family, css_name)
            embedded_css_name[font_family] = css_name if rules else None
            if rules:
                face_rules.append(rules)
        css_name = embedded_css_name[font_family]
        return f"'{css_name}', sans-serif" if css_name else "sans-serif"

    caption_font = resolve(theme.text.font_family)
    title_font = resolve(theme.title.font_family)
    return "".join(face_rules), caption_font, title_font


def _hex_rgba(hex_color: str, opacity_pct: int) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{opacity_pct / 100})"


def _photo_slide_html(photo: PhotoMetadata, href: str, caption_html: str) -> str:
    alt = html_lib.escape(photo.filename)
    caption_div = f'<div class="ps-caption">{caption_html}</div>' if caption_html else ""
    return (
        '<section class="ps-slide ps-photo">'
        '<div class="ps-frame">'
        f'<img data-src="{href}" alt="{alt}">'
        f'{caption_div}'
        '</div>'
        '</section>'
    )


def _title_slide_html(title_html: str) -> str:
    return (
        '<section class="ps-slide ps-title">'
        f'<div class="ps-title-box">{title_html}</div>'
        '</section>'
    )


def _build_css(theme: Theme, font_face_css: str, caption_font: str, title_font: str) -> str:
    text = theme.text
    title = theme.title

    caption_bg = (
        _hex_rgba(text.text_background_color, text.text_background_opacity)
        if text.text_background_enabled else "transparent"
    )
    title_bg = (
        _hex_rgba(title.text_background_color, title.text_background_opacity)
        if title.text_background_enabled else "transparent"
    )

    return f"""
{font_face_css}
:root{{
  --ps-bg:{theme.background.color};
  --ps-cap-color:{text.text_color};
  --ps-cap-bg:{caption_bg};
  --ps-cap-pad:{text.text_padding}px;
  --ps-cap-size:{text.base_font_size}px;
  --ps-cap-gap:{text.line_spacing}px;
  --ps-cap-font:{caption_font};
  --ps-title-color:{title.text_color};
  --ps-title-bg:{title_bg};
  --ps-title-pad:{title.text_padding}px;
  --ps-title-size:{title.base_font_size}px;
  --ps-title-gap:{title.line_spacing}px;
  --ps-title-align:{title.align};
  --ps-title-font:{title_font};
}}
*{{box-sizing:border-box;}}
html,body{{margin:0;padding:0;width:100%;height:100%;background:var(--ps-bg);overflow:hidden;
  font-family:var(--ps-cap-font);}}
#ps-stage{{position:relative;width:100vw;height:100vh;}}
.ps-slide{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  opacity:0;visibility:hidden;transition:opacity .6s ease;}}
.ps-slide.ps-active{{opacity:1;visibility:visible;}}
.ps-frame{{position:relative;display:inline-block;max-width:100vw;max-height:100vh;line-height:0;}}
.ps-frame img{{display:block;max-width:100vw;max-height:100vh;width:auto;height:auto;}}
.ps-caption{{position:absolute;left:0;right:0;bottom:0;color:var(--ps-cap-color);
  background:var(--ps-cap-bg);padding:var(--ps-cap-pad);font-size:var(--ps-cap-size);
  text-align:left;line-height:1.3;}}
.ps-caption .ps-line + .ps-line{{margin-top:var(--ps-cap-gap);}}
.ps-title-box{{color:var(--ps-title-color);background:var(--ps-title-bg);
  padding:var(--ps-title-pad);font-family:var(--ps-title-font);
  font-size:var(--ps-title-size);text-align:var(--ps-title-align);
  max-width:80vw;line-height:1.3;}}
.ps-title-box .ps-line + .ps-line{{margin-top:var(--ps-title-gap);}}
""".strip()


def _build_script(interval_seconds: float) -> str:
    interval_ms = int(round(interval_seconds * 1000))
    return f"""
(function(){{
  var INTERVAL_MS = {interval_ms};
  var slides = Array.prototype.slice.call(document.querySelectorAll('.ps-slide'));
  var current = 0;
  var timer = null;
  var playing = true;

  function loadImage(slide){{
    if (!slide) return;
    var img = slide.querySelector('img');
    if (img && img.dataset.src){{
      img.src = img.dataset.src;
      delete img.dataset.src;
    }}
  }}

  function unloadImage(slide){{
    if (!slide) return;
    var img = slide.querySelector('img');
    if (img && img.getAttribute('src')){{
      img.dataset.src = img.getAttribute('src');
      img.removeAttribute('src');
    }}
  }}

  function show(index){{
    current = ((index % slides.length) + slides.length) % slides.length;
    var activeSlide = slides[current];
    var nextSlide = slides[(current + 1) % slides.length];
    // Evict every slide except the new current/next, not just the single
    // slide the show was on before this call - back-and-forth navigation
    // (e.g. next, next, previous) can otherwise strand an earlier slide's
    // image loaded indefinitely, since it's neither "previous" nor
    // current/next at the moment its neighbor would have evicted it.
    slides.forEach(function(s){{
      s.classList.remove('ps-active');
      if (s !== activeSlide && s !== nextSlide){{ unloadImage(s); }}
    }});
    activeSlide.classList.add('ps-active');
    loadImage(activeSlide);
    loadImage(nextSlide);
  }}

  function scheduleNext(){{
    clearTimeout(timer);
    if (playing && slides.length > 1){{
      timer = setTimeout(function(){{ show(current + 1); scheduleNext(); }}, INTERVAL_MS);
    }}
  }}

  function togglePlay(){{
    playing = !playing;
    scheduleNext();
  }}

  document.addEventListener('click', togglePlay);
  document.addEventListener('keydown', function(e){{
    if (e.code === 'Space'){{ e.preventDefault(); togglePlay(); }}
    else if (e.key === 'ArrowRight'){{ show(current + 1); scheduleNext(); }}
    else if (e.key === 'ArrowLeft'){{ show(current - 1); scheduleNext(); }}
  }});

  if (slides.length){{
    show(0);
    scheduleNext();
  }}
}})();
""".strip()


def generate_html_slideshow(
    page_items: List[PageItem],
    text_label_associations: Optional[List[Tuple[PhotoMetadata, Optional[TextLabel]]]],
    theme: Theme,
    output_path: Path,
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
) -> Path:
    """
    Generate a single self-contained HTML slideshow file: one slide per page
    item (photo or title), in sequence order, with captions/titles styled
    from the active theme and photos referenced by relative path from
    output_path's own directory.

    Args:
        page_items: Ordered page items (photos and/or title slots) - e.g.
            the output of text_labels.merge_titles_with_photos
        text_label_associations: Optional list of (photo, text_label) tuples
            for captions - e.g. the output of
            text_labels.associate_text_labels_with_photos
        theme: Theme to style captions/titles/background from
        output_path: Full path (directory + filename) to write the .html file to
        interval_seconds: Seconds each slide is displayed before advancing

    Returns:
        output_path

    Raises:
        HtmlOutputError: If there are no page items, or the file can't be written
    """
    if not page_items:
        raise HtmlOutputError("No pages to output")

    output_dir = output_path.parent
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise HtmlOutputError(f"Could not create output directory {output_dir}: {e}")

    text_labels_map = {}
    if text_label_associations:
        for photo, label in text_label_associations:
            if label is not None:
                text_labels_map[photo.path] = label

    slides_html = []
    for item in page_items:
        if isinstance(item, TitleLabel):
            slides_html.append(_title_slide_html(_render_markdown_html(item.title)))
        else:
            href = _relative_href(item.path, output_dir)
            label = text_labels_map.get(item.path)
            caption_html = _render_markdown_html(label.text) if label else ""
            slides_html.append(_photo_slide_html(item, href, caption_html))

    font_face_css, caption_font, title_font = _resolve_theme_fonts(theme)
    css = _build_css(theme, font_face_css, caption_font, title_font)
    script = _build_script(interval_seconds)

    document = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_lib.escape(output_path.stem)}</title>
<style>{css}</style>
</head>
<body>
<div id="ps-stage">
{''.join(slides_html)}
</div>
<script>{script}</script>
</body>
</html>
"""

    try:
        output_path.write_text(document, encoding="utf-8")
    except OSError as e:
        raise HtmlOutputError(f"Failed to write html slideshow to {output_path}: {e}")

    logger.info(f"HTML slideshow with {len(slides_html)} slides saved to {output_path}")
    return output_path
