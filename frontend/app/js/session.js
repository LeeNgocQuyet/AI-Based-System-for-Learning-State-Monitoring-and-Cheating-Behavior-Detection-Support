/**
 * EduFocus — Session Timer
 * Uses setInterval to maintain an accurate elapsed-time counter.
 * State is persisted to sessionStorage so a page reload can recover.
 */

const TIMER_KEY_PREFIX = 'edufocus-timer-';

let _activeTimers = {};

/**
 * Format seconds to MM:SS or HH:MM:SS
 * @param {number} totalSeconds
 * @returns {string}
 */
export function formatTime(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;

  const pad = n => String(n).padStart(2, '0');

  if (h > 0) {
    return `${pad(h)}:${pad(m)}:${pad(sec)}`;
  }
  return `${pad(m)}:${pad(sec)}`;
}

/**
 * Load persisted timer state from sessionStorage.
 * @param {string} sessionId
 * @returns {{ elapsed: number, running: boolean, startedAt: number|null }}
 */
function loadTimerState(sessionId) {
  try {
    const raw = sessionStorage.getItem(TIMER_KEY_PREFIX + sessionId);
    if (raw) return JSON.parse(raw);
  } catch (e) {}
  return { elapsed: 0, running: false, startedAt: null };
}

/**
 * Persist timer state to sessionStorage.
 * @param {string} sessionId
 * @param {{ elapsed: number, running: boolean, startedAt: number|null }} state
 */
function saveTimerState(sessionId, state) {
  try {
    sessionStorage.setItem(TIMER_KEY_PREFIX + sessionId, JSON.stringify(state));
  } catch (e) {}
}

/**
 * Start or resume a timer for a session.
 * @param {string} sessionId
 * @param {function} onTick  Callback: (elapsed: number, formatted: string) => void
 * @returns {string}  timerId (same as sessionId)
 */
export function startTimer(sessionId, onTick) {
  // Stop any existing timer for this session
  stopTimer(sessionId);

  let state = loadTimerState(sessionId);
  // Calculate elapsed accounting for time passed since last save
  if (state.running && state.startedAt) {
    const extra = Math.floor((Date.now() - state.startedAt) / 1000);
    state.elapsed += extra;
  }
  state.running = true;
  state.startedAt = Date.now();
  saveTimerState(sessionId, state);

  let elapsed = state.elapsed;

  const id = setInterval(() => {
    elapsed++;
    const st = loadTimerState(sessionId);
    st.elapsed = elapsed;
    st.startedAt = Date.now();
    saveTimerState(sessionId, st);

    if (typeof onTick === 'function') {
      onTick(elapsed, formatTime(elapsed));
    }
  }, 1000);

  _activeTimers[sessionId] = id;

  // Immediately call onTick with current value
  if (typeof onTick === 'function') {
    onTick(elapsed, formatTime(elapsed));
  }

  return sessionId;
}

/**
 * Stop a timer.
 * @param {string} sessionId
 */
export function stopTimer(sessionId) {
  if (_activeTimers[sessionId]) {
    clearInterval(_activeTimers[sessionId]);
    delete _activeTimers[sessionId];
  }
  const state = loadTimerState(sessionId);
  if (state.running && state.startedAt) {
    const extra = Math.floor((Date.now() - state.startedAt) / 1000);
    state.elapsed += extra;
  }
  state.running = false;
  state.startedAt = null;
  saveTimerState(sessionId, state);
}

/**
 * Pause a timer (saves state without clearing it permanently).
 * @param {string} sessionId
 */
export function pauseTimer(sessionId) {
  if (_activeTimers[sessionId]) {
    clearInterval(_activeTimers[sessionId]);
    delete _activeTimers[sessionId];
  }
  const state = loadTimerState(sessionId);
  if (state.running && state.startedAt) {
    const extra = Math.floor((Date.now() - state.startedAt) / 1000);
    state.elapsed += extra;
  }
  state.running = false;
  state.startedAt = null;
  saveTimerState(sessionId, state);
}

/**
 * Resume a paused timer.
 * @param {string} sessionId
 * @param {function} onTick
 * @returns {string}
 */
export function resumeTimer(sessionId, onTick) {
  return startTimer(sessionId, onTick);
}

/**
 * Get current elapsed seconds for a session.
 * @param {string} sessionId
 * @returns {number}
 */
export function getElapsed(sessionId) {
  const state = loadTimerState(sessionId);
  let elapsed = state.elapsed;
  if (state.running && state.startedAt) {
    elapsed += Math.floor((Date.now() - state.startedAt) / 1000);
  }
  return elapsed;
}

/**
 * Clear timer state for a session.
 * @param {string} sessionId
 */
export function clearTimer(sessionId) {
  stopTimer(sessionId);
  try {
    sessionStorage.removeItem(TIMER_KEY_PREFIX + sessionId);
  } catch (e) {}
}

/**
 * Check if a timer is currently running.
 * @param {string} sessionId
 * @returns {boolean}
 */
export function isTimerRunning(sessionId) {
  return sessionId in _activeTimers;
}
