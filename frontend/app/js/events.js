/**
 * EduFocus — Page Visibility API & Event Logging
 * Tracks tab visibility changes during sessions.
 */

const EV_PREFIX = 'edufocus-events-';

/**
 * Initialize visibility tracking for a session.
 * @param {string} sessionId
 * @returns {Function} cleanup - call to stop tracking
 */
export function initVisibilityTracking(sessionId) {
  if (!sessionId) return () => {};
  let hiddenAt = null;

  function handleVisibilityChange() {
    const now = new Date();
    const isoTime = now.toISOString();
    const displayTime = now.toLocaleTimeString('vi-VN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    });

    if (document.hidden) {
      hiddenAt = Date.now();
      appendEvent(sessionId, {
        type: 'tab_hidden',
        timestamp: isoTime,
        displayTime,
        label: 'Rời khỏi tab',
        description: 'Trang học tập bị ẩn (chuyển tab hoặc thu nhỏ cửa sổ).'
      });
    } else {
      const duration = hiddenAt ? Date.now() - hiddenAt : null;
      hiddenAt = null;
      appendEvent(sessionId, {
        type: 'tab_visible',
        timestamp: isoTime,
        displayTime,
        label: 'Quay lại tab',
        description: duration != null
          ? `Quay lại trang học tập sau ${(duration / 1000).toFixed(1)} giây.`
          : 'Quay lại trang học tập.'
      });
    }
  }

  document.addEventListener('visibilitychange', handleVisibilityChange);
  return function cleanup() {
    document.removeEventListener('visibilitychange', handleVisibilityChange);
  };
}

function appendEvent(sessionId, event) {
  try {
    const key = EV_PREFIX + sessionId;
    const existing = JSON.parse(sessionStorage.getItem(key) || '[]');
    existing.push(event);
    sessionStorage.setItem(key, JSON.stringify(existing));
  } catch (e) { console.warn('appendEvent error', e); }
}

export function getSessionEvents(sessionId) {
  try {
    return JSON.parse(sessionStorage.getItem(EV_PREFIX + sessionId) || '[]');
  } catch (e) { return []; }
}

export function clearSessionEvents(sessionId) {
  try { sessionStorage.removeItem(EV_PREFIX + sessionId); } catch (e) {}
}

export function addManualEvent(sessionId, type, label, description) {
  const now = new Date();
  appendEvent(sessionId, {
    type, label, description,
    timestamp: now.toISOString(),
    displayTime: now.toLocaleTimeString('vi-VN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    })
  });
}
