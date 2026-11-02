import { fetchPlugSchedule, updatePlugSchedule } from "./api.js";

function formatCountdown(totalSeconds) {
  if (totalSeconds == null || Number.isNaN(totalSeconds)) {
    return "—";
  }
  const s = Math.max(0, Math.floor(totalSeconds));
  const mins = Math.floor(s / 60);
  const secs = s % 60;
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function readMinutes(input) {
  const value = parseInt(input.value, 10);
  if (Number.isNaN(value)) {
    return null;
  }
  return value;
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
  indicator.classList.remove("text-warning", "text-border-muted", "drop-shadow");
  if (plugOn) {
    indicator.classList.add("text-warning");
    indicator.style.filter = "drop-shadow(0 0 6px oklch(0.85 0.12 90))";
  } else {
    indicator.classList.add("text-border-muted");
    indicator.style.filter = "";
  }
}

function applyPanelState(panel, status, { disabled = false, message = "" } = {}) {
  const editRow = document.getElementById("plug_edit_row");
  const runRow = document.getElementById("plug_run_row");
  const interval = document.getElementById("plug_interval");
  const onDuration = document.getElementById("plug_on_duration");
  const statusEl = document.getElementById("plug_status");
  const countdownEl = document.getElementById("plug_countdown");
  const indicator = document.getElementById("plug_indicator");
  const powerBtn = document.getElementById("plug_power_toggle");

  const scheduleOn = Boolean(status.enabled);

  if (editRow && runRow) {
    editRow.classList.toggle("hidden", scheduleOn);
    editRow.classList.toggle("flex", !scheduleOn);
    runRow.classList.toggle("hidden", !scheduleOn);
    runRow.classList.toggle("flex", scheduleOn);
  }

  setPowerButtonStyle(powerBtn, scheduleOn);
  setIndicatorLight(indicator, Boolean(status.plug_on));

  if (!status.configured) {
    panel.classList.add("opacity-50");
    interval.disabled = true;
    onDuration.disabled = true;
    powerBtn.disabled = true;
    statusEl.classList.remove("hidden");
    statusEl.innerText = message || "Plug not configured (KASA_* env)";
    return;
  }

  panel.classList.toggle("opacity-50", Boolean(status.error && !scheduleOn));
  interval.disabled = disabled || scheduleOn;
  onDuration.disabled = disabled || scheduleOn;
  powerBtn.disabled = disabled;

  if (message) {
    statusEl.classList.remove("hidden");
    statusEl.innerText = message;
    return;
  }

  if (scheduleOn) {
    const countdown = formatCountdown(status.seconds_until_change);
    if (status.in_on_phase) {
      countdownEl.innerText = `ON for ${countdown}`;
    } else {
      countdownEl.innerText = `Next pulse in ${countdown}`;
    }
    if (status.error) {
      statusEl.classList.remove("hidden");
      statusEl.innerText = status.error;
    } else {
      statusEl.classList.add("hidden");
      statusEl.innerText = "";
    }
  } else if (status.error) {
    statusEl.classList.remove("hidden");
    statusEl.innerText = status.error;
  } else {
    statusEl.classList.add("hidden");
    statusEl.innerText = "";
  }
}

export function initPlugSchedule() {
  const panel = document.getElementById("plug_schedule_panel");
  if (!panel) {
    return;
  }

  const interval = document.getElementById("plug_interval");
  const onDuration = document.getElementById("plug_on_duration");
  const powerBtn = document.getElementById("plug_power_toggle");

  let lastStatus = null;
  let countdownSeconds = null;

  function syncCountdownFromStatus(status) {
    lastStatus = status;
    countdownSeconds = status.seconds_until_change;
    if (interval && document.activeElement !== interval) {
      interval.value = String(status.interval_minutes);
    }
    if (onDuration && document.activeElement !== onDuration) {
      onDuration.value = String(status.on_minutes);
    }
    applyPanelState(panel, {
      ...status,
      seconds_until_change: countdownSeconds,
    });
  }

  function tickCountdown() {
    if (!lastStatus?.enabled || countdownSeconds == null) {
      return;
    }
    if (countdownSeconds <= 0) {
      const enteringOnPhase = !lastStatus.in_on_phase;
      lastStatus = {
        ...lastStatus,
        in_on_phase: enteringOnPhase,
        plug_on: enteringOnPhase,
      };
      countdownSeconds = enteringOnPhase
        ? lastStatus.on_minutes * 60
        : lastStatus.interval_minutes * 60;
    } else {
      countdownSeconds -= 1;
    }
    applyPanelState(panel, {
      ...lastStatus,
      seconds_until_change: countdownSeconds,
    });
  }

  async function refresh() {
    try {
      const status = await fetchPlugSchedule();
      syncCountdownFromStatus(status);
    } catch (error) {
      console.error("Plug schedule error:", error);
      applyPanelState(
        panel,
        { configured: false, enabled: false, plug_on: null, error: null },
        { message: "Plug schedule unavailable" }
      );
    }
  }

  async function toggleSchedule() {
    const turnOn = !lastStatus?.enabled;
    const intervalMin = readMinutes(interval);
    const onMin = readMinutes(onDuration);
    if (intervalMin == null || onMin == null) {
      applyPanelState(panel, lastStatus || { configured: true, enabled: false }, {
        message: "Enter valid minute values",
      });
      return;
    }
    powerBtn.disabled = true;
    try {
      const status = await updatePlugSchedule({
        enabled: turnOn,
        interval_minutes: intervalMin,
        on_minutes: onMin,
      });
      syncCountdownFromStatus(status);
    } catch (error) {
      console.error("Plug schedule update:", error);
      applyPanelState(panel, lastStatus || { configured: true, enabled: false }, {
        message: error.message || "Update failed",
      });
    } finally {
      if (lastStatus) {
        applyPanelState(panel, {
          ...lastStatus,
          seconds_until_change: countdownSeconds,
        });
      }
    }
  }

  powerBtn.addEventListener("click", () => toggleSchedule());

  refresh();
  setInterval(refresh, 5000);
  setInterval(tickCountdown, 1000);
}
