## Context

Currently, the `LayoutPhoto` specification in `themes.py` relies on a scalar `size: float` value. In `renderer.py`, this single size value is applied to the page's usable width for landscape photos, and usable height for portrait photos. This single constraint makes it impossible to define bounds for both dimensions, which limits the flexibility of theme layouts and can result in photos overlapping or leaving too much white space, especially if the aspect ratio is extreme.

## Goals / Non-Goals

**Goals:**
- Update `LayoutPhoto` size in theme templates from a `float` to an object with `width` and `height` properties.
- Update `Theme.from_dict` and validation logic to strictly enforce this new format.
- Update the layout engine (`renderer.py`) to map these constraints to `target_width` and `target_height` without having to branch on the photo's orientation.

**Non-Goals:**
- Maintaining backward compatibility for the single-value size format. The user explicitly requested to drop support for the old format.
- Allowing arbitrary dimensional scaling options beyond proportional fitting. (Proportional scaling is already handled by `fit_photo_in_cell`).

## Decisions

1. **Schema Change:** Introduce a `LayoutPhotoSize` dataclass (or just a `dict`) with `width: float` and `height: float`. We will use a `LayoutPhotoSize` dataclass to maintain strict typing in `themes.py`. 
    - *Rationale:* Ensures robust validation when loading themes and makes the size abstraction clear.

2. **Validation:** In `themes.py` (`load_theme_file`), fail fast if `size` is not a dict containing both `width` and `height`.
    - *Rationale:* Dropping backward compatibility requires clear errors when loading an outdated theme.

3. **Renderer Updates:** In `renderer.py`'s `render_page_to_image`, remove the `if is_landscape` branch when calculating target dimensions. 
    - *Rationale:* We can calculate `target_width = int(usable_width * spec.size.width)` and `target_height = int(usable_height * spec.size.height)` directly. The existing `fit_photo_in_cell` algorithm will properly scale the image proportionally to fit within these dual boundaries.

## Risks / Trade-offs

- **[Risk]** Built-in and user themes will break. → **Mitigation:** We will update all built-in `.yaml` themes in `src/photobook_as_code/themes/` to use the new `{width: X, height: Y}` format.
- **[Risk]** Unexpected layout behavior due to strict max-bounds instead of one fixed bound. → **Mitigation:** Adjust the new `{width, height}` properties in the built-in themes to match the intent of the old layouts as closely as possible. For instance, if a landscape photo had a size of 0.8, it might now be `{width: 0.8, height: 1.0}`.