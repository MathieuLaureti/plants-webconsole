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

function applyPanelState(panel, status, { disabled = false, message = "" } = {}) {
  const interval = document.getElementById("plug_interval");
  const onDuration = document.getElementById("plug_on_duration");
  const statusEl = document.getElementById("plug_status");
  const startBtn = document.getElementById("plug_start");
  const stopBtn = document.getElementById("plug_stop");

  if (!status.configured) {
    panel.classList.add("opacity-50");
    interval.disabled = true;
    onDuration.disabled = true;
    startBtn.disabled = true;
    stopBtn.disabled = true;
    statusEl.innerText = message || "Plug not configured (KASA_* env)";
    return;
  }

  if (status.error && !status.enabled) {
    panel.classList.add("opacity-50");
  } else {
    panel.classList.remove("opacity-50");
  }

  interval.disabled = disabled || status.enabled;
  onDuration.disabled = disabled || status.enabled;
  startBtn.disabled = disabled || status.enabled;
  stopBtn.disabled = disabled || !status.enabled;

  const powerLabel =
    status.plug_on === null ? "Power unknown" : status.plug_on ? "Power ON" : "Power OFF";
  const phase = status.in_on_phase ? "pulse active" : "waiting";
  const countdown = formatCountdown(status.seconds_until_change);

  if (message) {
    statusEl.innerText = message;
    return;
  }
  if (status.enabled) {
    statusEl.innerText = `${powerLabel} · ${phase} · next change in ${countdown}`;
  } else if (status.error) {
    statusEl.innerText = status.error;
  } else {
    statusEl.innerText = `${powerLabel} · schedule stopped`;
  }
}

export function initPlugSchedule() {
  const panel = document.getElementById("plug_schedule_panel");
  if (!panel) {
    return;
  }

  const interval = document.getElementById("plug_interval");
  const onDuration = document.getElementById("plug_on_duration");
  const startBtn = document.getElementById("plug_start");
  const stopBtn = document.getElementById("plug_stop");

  let lastStatus = null;
  let countdownSeconds = null;
  let countdownTimer = null;

  function syncCountdownFromStatus(status) {
    lastStatus = status;
    countdownSeconds = status.seconds_until_change;
    if (interval && document.activeElement !== interval) {
      interval.value = String(status.interval_minutes);
    }
    if (onDuration && document.activeElement !== onDuration) {
      onDuration.value = String(status.on_minutes);
    }
    applyPanelState(panel, { ...status, seconds_until_change: countdownSeconds });
  }

  function tickCountdown() {
    if (!lastStatus?.enabled || countdownSeconds == null) {
      return;
    }
    countdownSeconds = Math.max(0, countdownSeconds - 1);
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

  async function submitSchedule(enabled) {
    const intervalMin = readMinutes(interval);
    const onMin = readMinutes(onDuration);
    if (intervalMin == null || onMin == null) {
      applyPanelState(panel, lastStatus || { configured: true }, {
        message: "Enter valid minute values",
      });
      return;
    }
    if (onMin >= intervalMin) {
      applyPanelState(panel, lastStatus || { configured: true, enabled: false }, {
        message: "ON duration must be shorter than the interval",
      });
      return;
    }
    startBtn.disabled = true;
    stopBtn.disabled = true;
    try {
      const status = await updatePlugSchedule({
        enabled,
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

  startBtn.addEventListener("click", () => submitSchedule(true));
  stopBtn.addEventListener("click", () => submitSchedule(false));

  refresh();
  setInterval(refresh, 15000);
  countdownTimer = setInterval(tickCountdown, 1000);
  panel.dataset.countdownTimer = countdownTimer;
}
