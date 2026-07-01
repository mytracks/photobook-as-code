## 1. Theme and Data Model Changes

- [ ] 1.1 Update theme YAML schema to require a `layouts` section.
- [ ] 1.2 Add data structures to `themes.py` to load and represent layout templates.
- [ ] 1.3 Add orientation detection to photo loading logic in `photos.py`.

## 2. Layout Engine Implementation

- [ ] 2.1 Implement the template matching algorithm in `layout.py` based on photo count and orientation.
- [ ] 2.2 Add logic to `layout.py` to prefer templates with exact orientation order matches.
- [ ] 2.3 Implement error handling in `layout.py` for when no matching template is found.
- [ ] 2.4 Remove the old grid-based layout calculation logic from `layout.py`.

## 3. Renderer Update

- [ ] 3.1 Modify the page rendering loop in `renderer.py` to use the new layout engine.
- [ ] 3.2 Update `renderer.py` to position and size photos based on the specifications from the matched layout template.
- [ ] 3.3 Ensure the renderer correctly handles aspect ratios when applying template sizing.

## 4. Theme Updates and Migration

- [ ] 4.1 Update the default themes (e.g., `clean`, `modern`, `classic`) to include `layouts` sections with a variety of templates.
- [ ] 4.2 Create a migration guide for users with custom themes, explaining the new `layouts` requirement.

## 5. Testing and Validation

- [ ] 5.1 Add unit tests for the new template matching logic in `layout.py`.
- [ ] 5.2 Add unit tests for the error handling when no template is found.
- [ ] 5.3 Add integration tests to verify that the renderer correctly applies layout templates.
- [ ] 5.4 Manually test the default themes with various photo combinations to ensure layouts are applied correctly.
