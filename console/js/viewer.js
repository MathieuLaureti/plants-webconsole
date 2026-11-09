export function initFullscreenViewer() {
  const modal = document.getElementById("fullscreen_modal");
  const closeBtn = document.getElementById("close_fullscreen");
  const viewport = document.getElementById("fullscreen_viewport");
  const transformLayer = document.getElementById("fullscreen_transform_layer");
  const fullscreenImg = document.getElementById("fullscreen_image");
  const zoomIndicator = document.getElementById("fullscreen_zoom_indicator");

  if (!modal || !closeBtn || !viewport || !transformLayer || !fullscreenImg) {
    return;
  }

  let scale = 1;
  let translateX = 0;
  let translateY = 0;

  // Touch tracking state
  let isTouching = false;
  let touchStartX = 0;
  let touchStartY = 0;
  let startTranslateX = 0;
  let startTranslateY = 0;
  let initialPinchDistance = 0;
  let initialPinchScale = 1;
  let initialPinchMidX = 0;
  let initialPinchMidY = 0;
  let lastTapTime = 0;

  // Mouse tracking state (desktop support)
  let isMouseDown = false;
  let mouseStartX = 0;
  let mouseStartY = 0;

  let indicatorTimer = null;

  function showZoomIndicator() {
    if (!zoomIndicator) return;
    zoomIndicator.innerText = `${Math.round(scale * 100)}%`;
    zoomIndicator.classList.remove("opacity-0");
    zoomIndicator.classList.add("opacity-100");
    if (indicatorTimer) clearTimeout(indicatorTimer);
    indicatorTimer = setTimeout(() => {
      zoomIndicator.classList.remove("opacity-100");
      zoomIndicator.classList.add("opacity-0");
    }, 1200);
  }

  function clampTranslation() {
    const maxPanX = Math.max(0, (window.innerWidth * (scale - 1)) / 2 + 40);
    const maxPanY = Math.max(0, (window.innerHeight * (scale - 1)) / 2 + 40);
    translateX = Math.max(-maxPanX, Math.min(maxPanX, translateX));
    translateY = Math.max(-maxPanY, Math.min(maxPanY, translateY));
  }

  function applyTransform(animate = false) {
    if (animate) {
      transformLayer.style.transition = "transform 0.25s cubic-bezier(0.25, 1, 0.5, 1)";
    } else {
      transformLayer.style.transition = "none";
    }
    transformLayer.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    showZoomIndicator();
  }

  function openFullscreen(src) {
    const triggerImage = document.getElementById("last_image_offset");
    const imageSrc = src || (triggerImage && triggerImage.tagName === "IMG" ? triggerImage.src : "");
    if (imageSrc) {
      fullscreenImg.src = imageSrc;
    }
    scale = 1;
    translateX = 0;
    translateY = 0;
    applyTransform(false);
    modal.classList.remove("hidden");
    document.body.style.overflow = "hidden";
  }

  function closeFullscreen() {
    modal.classList.add("hidden");
    document.body.style.overflow = "";
    scale = 1;
    translateX = 0;
    translateY = 0;
    applyTransform(false);
  }

  // Delegated click listener so dynamically replaced images also work seamlessly
  document.addEventListener("click", (e) => {
    const target = e.target;
    if (target && target.id === "last_image_offset" && target.tagName === "IMG") {
      openFullscreen(target.src);
    }
  });

  closeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    closeFullscreen();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.classList.contains("hidden")) {
      closeFullscreen();
    }
  });

  // Touch Gesture Listeners (Finger Pinch-to-Zoom & Pan)
  viewport.addEventListener(
    "touchstart",
    (e) => {
      if (modal.classList.contains("hidden")) return;

      if (e.touches.length === 1) {
        const now = Date.now();
        if (now - lastTapTime < 300) {
          // Double tap to toggle zoom
          e.preventDefault();
          if (scale > 1.2) {
            scale = 1;
            translateX = 0;
            translateY = 0;
          } else {
            scale = 2.5;
            const rect = viewport.getBoundingClientRect();
            const tapX = e.touches[0].clientX - rect.left - rect.width / 2;
            const tapY = e.touches[0].clientY - rect.top - rect.height / 2;
            translateX = -tapX * 0.8;
            translateY = -tapY * 0.8;
            clampTranslation();
          }
          applyTransform(true);
          lastTapTime = 0;
          return;
        }
        lastTapTime = now;

        isTouching = true;
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        startTranslateX = translateX;
        startTranslateY = translateY;
      } else if (e.touches.length === 2) {
        isTouching = false;
        const t1 = e.touches[0];
        const t2 = e.touches[1];
        initialPinchDistance = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
        initialPinchScale = scale;
        initialPinchMidX = (t1.clientX + t2.clientX) / 2;
        initialPinchMidY = (t1.clientY + t2.clientY) / 2;
        startTranslateX = translateX;
        startTranslateY = translateY;
      }
    },
    { passive: false }
  );

  viewport.addEventListener(
    "touchmove",
    (e) => {
      if (modal.classList.contains("hidden")) return;
      e.preventDefault(); // Prevent native mobile browser viewport zooming and page scrolling

      if (e.touches.length === 2 && initialPinchDistance > 0) {
        const t1 = e.touches[0];
        const t2 = e.touches[1];
        const currentDistance = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
        const pinchRatio = currentDistance / initialPinchDistance;
        scale = Math.min(Math.max(1, initialPinchScale * pinchRatio), 6);

        const currentMidX = (t1.clientX + t2.clientX) / 2;
        const currentMidY = (t1.clientY + t2.clientY) / 2;
        translateX = startTranslateX + (currentMidX - initialPinchMidX);
        translateY = startTranslateY + (currentMidY - initialPinchMidY);

        clampTranslation();
        applyTransform(false);
      } else if (e.touches.length === 1 && isTouching && scale > 1) {
        const deltaX = e.touches[0].clientX - touchStartX;
        const deltaY = e.touches[0].clientY - touchStartY;
        translateX = startTranslateX + deltaX;
        translateY = startTranslateY + deltaY;

        clampTranslation();
        applyTransform(false);
      }
    },
    { passive: false }
  );

  function handleTouchEnd(e) {
    if (e.touches.length === 1) {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
      startTranslateX = translateX;
      startTranslateY = translateY;
      isTouching = true;
      initialPinchDistance = 0;
    } else if (e.touches.length === 0) {
      isTouching = false;
      initialPinchDistance = 0;
      if (scale <= 1) {
        scale = 1;
        translateX = 0;
        translateY = 0;
        applyTransform(true);
      } else {
        clampTranslation();
        applyTransform(true);
      }
    }
  }

  viewport.addEventListener("touchend", handleTouchEnd);
  viewport.addEventListener("touchcancel", handleTouchEnd);

  // Desktop Mouse Wheel Zoom
  viewport.addEventListener(
    "wheel",
    (e) => {
      if (modal.classList.contains("hidden")) return;
      e.preventDefault();

      const zoomFactor = e.deltaY < 0 ? 1.25 : 0.8;
      const targetScale = Math.min(Math.max(1, scale * zoomFactor), 6);

      if (targetScale === 1) {
        scale = 1;
        translateX = 0;
        translateY = 0;
      } else {
        const rect = viewport.getBoundingClientRect();
        const cursorX = e.clientX - rect.left - rect.width / 2;
        const cursorY = e.clientY - rect.top - rect.height / 2;
        const scaleChange = targetScale / scale;
        translateX = cursorX - (cursorX - translateX) * scaleChange;
        translateY = cursorY - (cursorY - translateY) * scaleChange;
        scale = targetScale;
        clampTranslation();
      }
      applyTransform(true);
    },
    { passive: false }
  );

  // Desktop Mouse Drag to Pan
  viewport.addEventListener("mousedown", (e) => {
    if (modal.classList.contains("hidden")) return;
    if (e.button !== 0) return;
    if (scale > 1) {
      isMouseDown = true;
      mouseStartX = e.clientX;
      mouseStartY = e.clientY;
      startTranslateX = translateX;
      startTranslateY = translateY;
      viewport.classList.add("is-dragging");
    }
  });

  window.addEventListener("mousemove", (e) => {
    if (!isMouseDown || scale <= 1) return;
    const deltaX = e.clientX - mouseStartX;
    const deltaY = e.clientY - mouseStartY;
    translateX = startTranslateX + deltaX;
    translateY = startTranslateY + deltaY;
    clampTranslation();
    applyTransform(false);
  });

  window.addEventListener("mouseup", () => {
    if (isMouseDown) {
      isMouseDown = false;
      viewport.classList.remove("is-dragging");
      clampTranslation();
      applyTransform(true);
    }
  });

  return { openFullscreen, closeFullscreen };
}
