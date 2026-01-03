async function getLatestOffset(offset,camera_id) {
  const url = `https://homelabdu204.ca/plants/api/get_last_image/${offset}/${camera_id}`;
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    const image_info = await response.json();

    console.log(image_info["timestamp"]);
    console.log(image_info["url"]);

    document.getElementById("timestamp").innerText = image_info["timestamp"];
    document.getElementById("last_image_offset").src = image_info["url"];
  } catch (error) {
    console.error(error.message);
  }
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function get_slideshow(mode) {
  const url = `https://homelabdu204.ca/plants/api/slideshow/${mode}`;
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    const images_info = await response.json();
    console.log(images_info["images"]);

    for (const image_data of images_info["images"]) {
      document.getElementById("timestamp").innerText = image_data["timestamp"];
      document.getElementById("last_image_offset").src = image_data["url"];
      console.log(`Showing image ${image_data["timestamp"]} of ${image_data["url"]}`);

      // Wait for the specified delay before continuing to the next image
      await sleep(100);
    }

  } catch (error) {
    console.error(error.message);
  }
}