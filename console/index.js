async function getLatest() {
  const url = "https://192.168.2.109:445/get_last_image";
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    const image_url = await response.json();
    console.log(image_url)
    document.getElementById("last_image").src = image_url["url"]
  } catch (error) {
    console.error(error.message);
  }
}

async function getLatestOffset(offset) {
  const url = `https://192.168.2.109:445/get_last_image/${offset}`;
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    const image_url = await response.json();

    document.getElementById("last_image_offset").src = image_url["url"]
  } catch (error) {
    console.error(error.message);
  }
}

