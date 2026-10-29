import { fetchLastImage, fetchTimelapse } from "./api.js";

export function createGalleryController() {
  let offset = 0;
  let cameraId = 1;
  let mode = "day";

  async function getLatestOffset(off = offset, cam = cameraId) {
    let displayElement = document.getElementById("last_image_offset");

    if (displayElement.tagName === "VIDEO") {
      if (displayElement.src.startsWith("blob:")) {
        URL.revokeObjectURL(displayElement.src);
      }
      const img = document.createElement("img");
      img.id = "last_image_offset";
      img.className =
        "bg-bg-light border border-border w-full rounded-xl h-full";
      displayElement.parentNode.replaceChild(img, displayElement);
      displayElement = img;
    }

    try {
      const imageInfo = await fetchLastImage(off, cam);
      document.getElementById("timestamp").innerText = imageInfo.timestamp;
      displayElement.src = imageInfo.url;
    } catch (error) {
      console.error("Fetch error:", error.message);
      document.getElementById("timestamp").innerText = "ERROR LOADING IMAGE";
    }
  }

  async function getSlideshow(limit, cam = cameraId) {
    const displayContainer = document.getElementById(
      "last_image_offset"
    ).parentElement;
    const timestampBtn = document.getElementById("timestamp");

    try {
      timestampBtn.innerText = "GENERATING...";
      const blob = await fetchTimelapse(cam, limit);
      const videoUrl = URL.createObjectURL(blob);
      let currentElement = document.getElementById("last_image_offset");

      if (currentElement.tagName === "IMG") {
        const video = document.createElement("video");
        video.id = "last_image_offset";
        video.className =
          "bg-bg-light border border-border w-full rounded-xl h-full object-contain";
        video.controls = true;
        video.autoplay = true;
        currentElement.parentNode.replaceChild(video, currentElement);
        currentElement = video;
      }

      if (currentElement.src && currentElement.src.startsWith("blob:")) {
        URL.revokeObjectURL(currentElement.src);
      }

      currentElement.src = videoUrl;
      currentElement.play();
      timestampBtn.innerText = "TIMELAPSE LOADED";
    } catch (error) {
      console.error("Timelapse error:", error);
      timestampBtn.innerText = "ERROR";
    }
  }

  function wireControls() {
    document.getElementById("next").addEventListener("click", () => {
      offset++;
      getLatestOffset(offset, cameraId);
    });

    document.getElementById("prev").addEventListener("click", () => {
      if (offset > 0) {
        offset--;
        getLatestOffset(offset, cameraId);
      }
    });

    document.getElementById("camera_button").addEventListener("click", () => {
      if (cameraId >= 2) {
        cameraId = 1;
      } else {
        cameraId++;
      }
      document.getElementById("camera_button").innerText = `Camera ${cameraId}`;
      offset = 0;
      getLatestOffset(offset, cameraId);
    });

    document.getElementById("day_week_month").addEventListener("click", () => {
      if (mode === "day") {
        mode = "week";
        document.getElementById("day_week_month").innerText = "week";
      } else if (mode === "week") {
        mode = "month";
        document.getElementById("day_week_month").innerText = "month";
      } else {
        mode = "day";
        document.getElementById("day_week_month").innerText = "day";
      }
      offset = 0;
    });

    document.getElementById("slideshow").addEventListener("click", () => {
      let limit = 30;
      if (mode === "week") {
        limit = 210;
      } else if (mode === "month") {
        limit = 840;
      }
      getSlideshow(limit, cameraId);
    });

    document.getElementById("timestamp").addEventListener("click", () => {
      offset = 0;
      getLatestOffset(0, cameraId);
    });

    getLatestOffset(offset, cameraId);
  }

  return { wireControls };
}
