## 1. Backend

- [ ] 1.1 Add `lat`/`lon` (or `None`/`None`) to `view_item`'s `common_context` in `app.py`, sourced from `data.photo_at(index).gps` when `has_gps` is true; verify with a test asserting the rendered page's open-in-Maps link href contains the photo's coordinates for a GPS-tagged fixture photo, and that no such href is rendered for a photo without GPS

## 2. Icon

- [ ] 2.1 Add a new `icon-map` `<symbol>` to the SVG sprite in `editor.html`, styled consistently with the existing `icon-geo`/`icon-plus` line icons

## 3. Template

- [ ] 3.1 Add the open-in-Maps control to `editor.html`'s header, positioned immediately after `geo-button` and before `add-title-button`: an `<a>` with `href="https://maps.apple.com/?ll={{ lat }},{{ lon }}&q={{ lat }},{{ lon }}"`, `target="_blank"`, `rel="noopener"`, an accessible label, and the `icon-map` icon when `has_gps` is true; when false, omit `href` and set `aria-disabled="true"` plus a `title` explaining why, mirroring the nav-prev/nav-next disabled-anchor pattern
- [ ] 3.2 Verify the control is absent entirely for title items (not just disabled), matching the existing geo-button's title-item behavior

## 4. Verification

- [ ] 4.1 Add/extend a test asserting the control is not rendered for title items, is rendered enabled with the correct Apple Maps href for a GPS-tagged photo, and is rendered disabled (no href, `aria-disabled="true"`) for a photo without GPS
- [ ] 4.2 Run the full test suite and confirm no regressions to the existing reverse-geocode button's rendering or position (still immediately before add-title)
- [ ] 4.3 Manually exercise the control in a browser: click it for a GPS-tagged photo and confirm a new tab opens to the expected Apple Maps location
