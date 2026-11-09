# feat(console): fullscreen image modal with pinch-to-zoom and persistent close button

## 1. Context & Objective
- **Problem Statement**: Plant console users viewing the live plant camera preview on mobile and desktop cannot inspect fine details because the image is confined to a fixed container without zoom or fullscreen viewing capabilities.
- **Target Outcome**: Clicking the plant preview image opens an immersive fullscreen overlay with finger pinch-to-zoom and pan gestures, featuring a persistent "X" close button in the top right corner that always returns the user to the main page.
- **Issue Reference / Dependencies**: Builds upon live camera preview in `console/index.html` and `console/js/gallery.js`.

## 2. Scope Boundaries
- **In-Scope**:
  - Click/tap handler on `#last_image_offset` to open full-viewport overlay modal.
  - Fullscreen overlay with dark backdrop blur, keeping current image src and preserving 180° orientation.
  - Multi-touch finger pinch-to-zoom gesture handling (`touchstart`, `touchmove`, `touchend`, `touchcancel`) with smooth scaling (1x to 6x) and pan positioning.
  - Desktop mouse wheel zoom and pan drag support for cross-platform convenience and testing.
  - High-visibility "X" close button fixed at the top right corner of the screen, always accessible regardless of zoom level or pan position.
  - Escape key listener and backdrop click behavior to return to main page.
  - Seamless integration with ES module structure (`console/js/viewer.js`, `console/js/gallery.js`, `console/js/main.js`).
- **Out-of-Scope**:
  - Server-side image manipulation or backend API changes.
  - Modifying temperature/humidity charts or sensor scanning routines.
  - Altering slideshow autoplay timing logic.

## 3. Technical Blueprint & Affected Files
| Component / File Path | Target Action | Details |
| :--- | :--- | :--- |
| `console/index.html` | `Modify` | Add fullscreen modal markup, persistent close button with "X" icon, add cursor styling to `#last_image_offset`. |
| `console/js/viewer.js` | `Create` | Implement `initFullscreenViewer()` with touch pinch-to-zoom, pan drag, wheel zoom, double-tap, and close/reset handlers. |
| `console/js/gallery.js` | `Modify` | Sync fullscreen image src during image updates and maintain rotation/hover classes on restored image element. |
| `console/js/main.js` | `Modify` | Import and invoke `initFullscreenViewer()` in application lifecycle. |
| `console/css/style.css` | `Modify` | Add touch gesture helper styles (`touch-action: none`, smooth transform transition classes). |
| `docs/work/active-slice.yaml` | `Modify` | Enroll `fullscreen-image-zoom` slice linking to issue #10. |

### Implementation Steps
1. **Step 1 - Markup & Styles (`console/index.html`, `console/css/style.css`)**:
   - Add `#fullscreen_modal` overlay with `fixed inset-0 z-50 bg-bg-dark/95 backdrop-blur-md hidden flex items-center justify-center overflow-hidden`.
   - Add top-right close button `#close_fullscreen` with `fixed top-4 right-4 z-[70]` with high contrast, large touch area (min 48x48px), and clear "✕" symbol.
   - Add image container `#fullscreen_viewport` and image `#fullscreen_image` with `rotate-180` to preserve physical camera mounting orientation.
2. **Step 2 - Gesture Engine (`console/js/viewer.js`)**:
   - Implement touch handlers: calculate distance between two touches for pinch-to-zoom; calculate movement delta for one-finger pan when zoomed in; calculate touch centers to zoom toward pinch focus.
   - Implement mouse wheel zoom and mouse drag support as desktop fallback.
   - Reset transforms (scale 1, translate 0, 0) on open and close.
   - Implement close handler on `#close_fullscreen` and `keydown` Escape.
3. **Step 3 - Gallery & Main Integration (`console/js/gallery.js`, `console/js/main.js`)**:
   - Register fullscreen viewer initialization in `bootApp()`.
   - Sync `fullscreen_image.src` when newer camera offsets are fetched.

## 4. Acceptance Criteria
- [ ] Clicking on `#last_image_offset` opens the fullscreen image viewer overlay.
- [ ] The fullscreen view displays the same source image currently loaded in `#last_image_offset`.
- [ ] The fullscreen image maintains the proper 180° rotation matching the camera setup.
- [ ] An "X" close button is fixed and visible in the top right corner over the image at all times, including when zoomed in or panned.
- [ ] Clicking or tapping the "X" button closes the fullscreen view and returns to the main page.
- [ ] Pressing the Escape key closes the fullscreen view and returns to the main page.
- [ ] Two-finger pinch gesture zooms the image in and out between 1x and 6x scale.
- [ ] When zoomed (> 1x), one-finger touch drags pan the image across the screen smoothly.
- [ ] Zoom and pan state resets cleanly to 1x scale and (0,0) offset when the modal is closed and reopened.
- [ ] Body scrolling is locked while the fullscreen modal is open and restored upon closing.

## 5. Verification & Testing
- **Local Reproduction / Test Commands**:
  ```bash
  # Validate JavaScript syntax
  node --check console/js/viewer.js
  node --check console/js/gallery.js
  node --check console/js/main.js
  ```
- **Edge Cases & Failure Modes**:
  - Rapid pinch-in below 1x: Clamped to 1x min scale to prevent image inversion or disappearing.
  - Pinch-out past maximum: Clamped to 6x max scale.
  - Single finger pan when scale is 1x: Ignored so image stays centered.
  - Fast touch cancellation (`touchcancel`): Resets touch tracking variables cleanly without NaN state.
  - Dynamic element replacement: Delegated event listener ensures clicks on `#last_image_offset` work even after video/image toggling.

## 6. Execution Notes for Agents & Developers
- **Branch Naming**: `feat/fullscreen-image-zoom`
- **Labels**: `enhancement`, `agent-managed`
- **Dependencies**: No external npm/pip dependencies added; uses native Touch and Pointer events with existing Tailwind CSS.
