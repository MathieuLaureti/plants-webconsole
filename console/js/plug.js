import {
  createPlug,
  fetchPlugRuntime,
  listPlugs,
  setPlugScheduleEnabled,
  updatePlug,
} from "./api.js";

const STORAGE_KEY = "plug_selected_id";

function formatCountdown(totalSeconds) {
  if (totalSeconds == null || Number.isNaN(totalSeconds)) {
    return "—";
  }
  const s = Math.max(0, Math.floor(totalSeconds));
  const mins = Math.floor(s / 60);
  const secs = s % 60;
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function timeInputToHhmm(value) {
  if (!value) {
    return "07:00";
  }
  return value.length === 5 ? value : value.slice(0, 5);
}

function hhmmToTimeInput(hhmm) {
  return hhmm || "07:00";
}

function setPowerButtonStyle(btn, scheduleOn) {
  btn.classList.remove("border-success", "bg-success/30", "border-danger", "bg-danger/25");
  if (scheduleOn) {
    btn.classList.add("border-success", "bg-success/30");
    btn.title = "Schedule on — click to stop";
  } else {
    btn.classList.add("border-danger", "bg-danger/25");
    btn.title = "Schedule off — click to start";
  }
}

function setIndicatorLight(indicator, plugOn) {
  indicator.classList.remove("text-warning", "text-border-muted");
  if (plugOn) {
    indicator.classList.add("text-warning");
    indicator.style.filter = "drop-shadow(0 0 6px oklch(0.85 0.12 90))";
  } else {
    indicator.classList.add("text-border-muted");
    indicator.style.filter = "";
  }
}

export function initPlugSchedule() {
  const panel = document.getElementById("plug_schedule_panel");
  const select = document.getElementById("plug_select");
  const addBtn = document.getElementById("plug_add");
  const editBtn = document.getElementById("plug_edit");
  const powerBtn = document.getElementById("plug_power_toggle");
  const runRow = document.getElementById("plug_run_row");
  const countdownEl = document.getElementById("plug_countdown");
  const indicator = document.getElementById("plug_indicator");
  const statusEl = document.getElementById("plug_status");

  const backdrop = document.getElementById("plug_modal_backdrop");
  const form = document.getElementById("plug_form");
  const modalTitle = document.getElementById("plug_modal_title");
  const formError = document.getElementById("plug_form_error");
  const simplePanel = document.getElementById("plug_form_simple");
  const advancedPanel = document.getElementById("plug_form_advanced");
  const timeList = document.getElementById("plug_time_list");
  const timeAddBtn = document.getElementById("plug_time_add");
  const cancelBtn = document.getElementById("plug_form_cancel");

  if (!panel || !select) {
    return;
  }

  let plugs = [];
  let selectedId = sessionStorage.getItem(STORAGE_KEY) || "";
  let editingId = null;
  let lastRuntime = null;
  let countdownSeconds = null;

  function selectedPlug() {
    return plugs.find((p) => String(p.id) === String(selectedId));
  }

  function showError(msg) {
    statusEl.classList.remove("hidden");
    statusEl.innerText = msg;
  }

  function clearError() {
    statusEl.classList.add("hidden");
    statusEl.innerText = "";
  }

  function populateSelect() {
    const prev = select.value;
    select.innerHTML = "";
    if (plugs.length === 0) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "No plugs";
      select.appendChild(opt);
      selectedId = "";
    } else {
      for (const plug of plugs) {
        const opt = document.createElement("option");
        opt.value = String(plug.id);
        opt.textContent = plug.title;
        select.appendChild(opt);
      }
      if (plugs.some((p) => String(p.id) === String(selectedId))) {
        select.value = String(selectedId);
      } else {
        selectedId = String(plugs[0].id);
        select.value = selectedId;
      }
    }
    sessionStorage.setItem(STORAGE_KEY, selectedId);
    editBtn.disabled = !selectedId;
    powerBtn.disabled = !selectedId;
    if (prev !== select.value) {
      refreshRuntime();
    }
  }

  function applyRuntimeUi() {
    const plug = selectedPlug();
    const enabled = Boolean(plug?.schedule_enabled);
    setPowerButtonStyle(powerBtn, enabled);
    runRow.classList.toggle("hidden", !enabled);
    runRow.classList.toggle("flex", enabled);

    if (!enabled || !lastRuntime) {
      return;
    }

    setIndicatorLight(indicator, Boolean(lastRuntime.plug_on));
    const countdown = formatCountdown(countdownSeconds);
    if (lastRuntime.in_on_phase) {
      countdownEl.innerText = `ON for ${countdown}`;
    } else {
      countdownEl.innerText = `Next pulse in ${countdown}`;
    }
    if (lastRuntime.error) {
      showError(lastRuntime.error);
    } else {
      clearError();
    }
  }

  async function loadPlugs() {
    try {
      plugs = await listPlugs();
      populateSelect();
      applyRuntimeUi();
    } catch (error) {
      showError(error.message || "Failed to load plugs");
    }
  }

  async function refreshRuntime() {
    if (!selectedId) {
      lastRuntime = null;
      applyRuntimeUi();
      return;
    }
    try {
      lastRuntime = await fetchPlugRuntime(selectedId);
      countdownSeconds = lastRuntime.seconds_until_change;
      applyRuntimeUi();
    } catch (error) {
      showError(error.message || "Runtime unavailable");
    }
  }

  function tickCountdown() {
    const plug = selectedPlug();
    if (!plug?.schedule_enabled || countdownSeconds == null) {
      return;
    }
    if (countdownSeconds <= 0) {
      refreshRuntime();
      return;
    }
    countdownSeconds -= 1;
    applyRuntimeUi();
  }

  function setMode(mode) {
    const isSimple = mode === "simple";
    simplePanel.classList.toggle("hidden", !isSimple);
    advancedPanel.classList.toggle("hidden", isSimple);
    form.querySelectorAll('input[name="plug_form_mode"]').forEach((el) => {
      el.checked = el.value === mode;
    });
  }

  function addTimeRow(value = "08:00") {
    const li = document.createElement("li");
    li.className = "flex gap-2 items-center";
    li.innerHTML = `<input type="time" value="${value}" class="plug-time-entry flex-1 bg-bg-light border border-border rounded-lg p-1 text-text text-sm" />
      <button type="button" class="plug-time-remove text-danger text-xs border border-border rounded px-2">×</button>`;
    li.querySelector(".plug-time-remove").addEventListener("click", () => li.remove());
    timeList.appendChild(li);
  }

  function readSimpleSchedule() {
    return {
      morning_time: timeInputToHhmm(document.getElementById("plug_simple_morning").value),
      night_time: timeInputToHhmm(document.getElementById("plug_simple_night").value),
      day_pulse_count: parseInt(document.getElementById("plug_simple_day_count").value, 10),
      night_pulse_count: parseInt(document.getElementById("plug_simple_night_count").value, 10),
      pulse_seconds: parseInt(document.getElementById("plug_simple_pulse").value, 10),
    };
  }

  function readAdvancedSchedule() {
    const times = [...timeList.querySelectorAll(".plug-time-entry")].map((el) =>
      timeInputToHhmm(el.value)
    );
    return {
      pulse_seconds: parseInt(document.getElementById("plug_advanced_pulse").value, 10),
      times,
    };
  }

  function openModal({ plug = null } = {}) {
    editingId = plug ? plug.id : null;
    modalTitle.innerText = plug ? "Edit plug" : "New plug";
    formError.classList.add("hidden");
    document.getElementById("plug_form_host").value = plug?.host || "";
    document.getElementById("plug_form_title").value = plug?.title || "";
    document.getElementById("plug_form_description").value = plug?.description || "";
    const mode = plug?.schedule_type || "simple";
    setMode(mode);
    const schedule = plug?.schedule || {};
    if (mode === "simple") {
      document.getElementById("plug_simple_morning").value = hhmmToTimeInput(
        schedule.morning_time || "07:00"
      );
      document.getElementById("plug_simple_night").value = hhmmToTimeInput(
        schedule.night_time || "20:00"
      );
      document.getElementById("plug_simple_day_count").value = schedule.day_pulse_count ?? 14;
      document.getElementById("plug_simple_night_count").value = schedule.night_pulse_count ?? 4;
      document.getElementById("plug_simple_pulse").value = schedule.pulse_seconds ?? 60;
    } else {
      document.getElementById("plug_advanced_pulse").value = schedule.pulse_seconds ?? 60;
      timeList.innerHTML = "";
      const times = schedule.times?.length ? schedule.times : ["08:00", "12:00"];
      times.forEach((t) => addTimeRow(hhmmToTimeInput(t)));
    }
    backdrop.classList.remove("hidden");
  }

  function closeModal() {
    backdrop.classList.add("hidden");
    editingId = null;
  }

  form.querySelectorAll('input[name="plug_form_mode"]').forEach((el) => {
    el.addEventListener("change", () => setMode(el.value));
  });

  timeAddBtn.addEventListener("click", () => addTimeRow());
  cancelBtn.addEventListener("click", closeModal);
  addBtn.addEventListener("click", () => {
    timeList.innerHTML = "";
    addTimeRow("08:00");
    openModal();
  });
  editBtn.addEventListener("click", () => {
    const plug = selectedPlug();
    if (plug) {
      openModal({ plug });
    }
  });

  select.addEventListener("change", () => {
    selectedId = select.value;
    sessionStorage.setItem(STORAGE_KEY, selectedId);
    editBtn.disabled = !selectedId;
    powerBtn.disabled = !selectedId;
    refreshRuntime();
  });

  powerBtn.addEventListener("click", async () => {
    const plug = selectedPlug();
    if (!plug) {
      return;
    }
    powerBtn.disabled = true;
    try {
      const enabled = !plug.schedule_enabled;
      await setPlugScheduleEnabled(plug.id, enabled);
      await loadPlugs();
      await refreshRuntime();
    } catch (error) {
      showError(error.message || "Toggle failed");
    } finally {
      powerBtn.disabled = !selectedId;
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    formError.classList.add("hidden");
    const mode = form.querySelector('input[name="plug_form_mode"]:checked').value;
    const payload = {
      host: document.getElementById("plug_form_host").value.trim(),
      title: document.getElementById("plug_form_title").value.trim(),
      description: document.getElementById("plug_form_description").value.trim() || null,
      schedule_type: mode,
      schedule: mode === "simple" ? readSimpleSchedule() : readAdvancedSchedule(),
    };
    try {
      if (editingId) {
        await updatePlug(editingId, payload);
      } else {
        const created = await createPlug(payload);
        selectedId = String(created.id);
      }
      closeModal();
      await loadPlugs();
      await refreshRuntime();
    } catch (error) {
      formError.innerText = error.message || "Save failed";
      formError.classList.remove("hidden");
    }
  });

  loadPlugs();
  setInterval(refreshRuntime, 5000);
  setInterval(tickCountdown, 1000);
}
