import { clearToken, getToken, login } from "./auth.js";
import { startChartPolling } from "./charts.js";
import { createGalleryController } from "./gallery.js";
import { initPlugToggle } from "./plug.js";

function showLogin(show) {
  const login = document.getElementById("login_panel");
  const app = document.getElementById("app_main");
  if (show) {
    login.classList.remove("hidden");
    app.classList.add("hidden");
  } else {
    login.classList.add("hidden");
    app.classList.remove("hidden");
  }
}

function bindLoginForm() {
  const form = document.getElementById("login_form");
  const errorEl = document.getElementById("login_error");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorEl.classList.add("hidden");
    const username = document.getElementById("login_username").value;
    const password = document.getElementById("login_password").value;
    try {
      await login(username, password);
      bootApp();
    } catch (error) {
      errorEl.innerText = error.message || "Login failed";
      errorEl.classList.remove("hidden");
    }
  });
}

function bootApp() {
  showLogin(false);
  startChartPolling();
  createGalleryController().wireControls();
  initPlugToggle();
}

function boot() {
  bindLoginForm();
  window.addEventListener("auth:logout", () => {
    showLogin(true);
  });
  if (getToken()) {
    bootApp();
  } else {
    showLogin(true);
  }
}

boot();
