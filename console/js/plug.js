import { fetchPlugState, setPlugPower } from "./api.js";

function updateButton(btn, state) {
  if (state.error) {
    btn.disabled = true;
    btn.classList.add("opacity-50");
    btn.title = state.error;
    if (state.error.includes("Third-Party")) {
      btn.innerText = "Enable 3rd-party in Kasa app";
    } else if (!state.configured) {
      btn.innerText = "Plug N/A";
    } else {
      btn.innerText = "Plug setup needed";
    }
    return;
  }
  if (!state.configured) {
    btn.disabled = true;
    btn.innerText = "Plug N/A";
    btn.classList.add("opacity-50");
    return;
  }
  btn.disabled = false;
  btn.classList.remove("opacity-50");
  btn.title = "";
  btn.innerText = state.on ? "Power: ON" : "Power: OFF";
  btn.dataset.on = state.on ? "1" : "0";
}

export function initPlugToggle() {
  const btn = document.getElementById("plug_toggle");
  if (!btn) {
    return;
  }

  async function refresh() {
    try {
      const state = await fetchPlugState();
      updateButton(btn, state);
    } catch (error) {
      console.error("Plug state error:", error);
      btn.disabled = true;
      btn.innerText = "Plug ERR";
    }
  }

  btn.addEventListener("click", async () => {
    if (btn.disabled) {
      return;
    }
    const turnOn = btn.dataset.on !== "1";
    btn.disabled = true;
    btn.innerText = "...";
    try {
      const state = await setPlugPower(turnOn);
      updateButton(btn, state);
    } catch (error) {
      console.error("Plug toggle error:", error);
      await refresh();
    }
  });

  refresh();
  setInterval(refresh, 60000);
}
