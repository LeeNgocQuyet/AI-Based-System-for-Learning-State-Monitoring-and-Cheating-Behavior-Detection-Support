/**
 * EduFocus — Student Live Session Page
 * Real session timer + Page Visibility tracking + live webcam preview.
 */

import { renderShell } from './shell.js';
import { getSession, getCourse, studentJoinSession } from '../data.js';
import { getCurrentUser } from '../auth.js';
import { esc, badge, btn, toast, initials } from '../ui.js';
import { navigate, getParam } from '../router.js';
import { startTimer, pauseTimer, resumeTimer, stopTimer, formatTime, clearTimer, isTimerRunning } from '../session.js';
import { initVisibilityTracking, getSessionEvents, addManualEvent, clearSessionEvents } from '../events.js';
import { attachToVideo, stopCurrentCamera } from '../camera.js';

let _timerId     = null;
let _paused      = false;
let _cleanupVis  = null;
let _sessionId   = null;
let _liveStream  = null;

export function renderStudentLive(params = {}) {
  const sessionId = params.sessionId || getParam('sessionId');
  const courseId  = params.courseId  || getParam('courseId');
  const s = getSession(sessionId);
  const c = s ? getCourse(s.courseId || courseId) : null;
  const user = getCurrentUser();

  _sessionId = sessionId;

  if (!s || s.status !== 'Đang diễn ra') {
    return renderShell(`
<div class="empty">
  <h3>Phiên không còn hoạt động</h3>
  <p>Phiên học này đã kết thúc hoặc không tồn tại.</p>
  ${btn('Về trang chủ', 'student-home', 'primary')}
</div>`, 'student-home');
  }

  const events = getSessionEvents(sessionId);

  const content = `
<div class="page-head">
  <div>
    <div class="eyebrow">PHIÊN ĐANG DIỄN RA</div>
    <h1 class="h1">${esc(s.title)}</h1>
    <p class="sub">${esc(c ? c.name : '')} · ${esc(s.type)} · ${s.duration} phút</p>
  </div>
  <div class="toolbar">
    ${badge(s.type, s.type === 'Phiên thi' ? 'b-purple' : 'b-blue')}
    ${badge('Đang diễn ra', 'b-green')}
  </div>
</div>

<div class="live-session-layout">
  <!-- Camera panel -->
  <div class="card" style="overflow:hidden;border-radius:16px">
    <div class="live-camera-panel" id="live-camera-panel">
      <video id="live-video" autoplay muted playsinline style="width:100%;height:100%;object-fit:cover;display:none;border-radius:16px"></video>
      <div id="live-camera-placeholder" style="display:flex;align-items:center;justify-content:center;flex-direction:column;gap:8px;color:#8da995;padding:40px;text-align:center">
        <span style="font-size:36px">📷</span>
        <strong>Camera không được kích hoạt</strong>
        <span style="font-size:12px">Camera của bạn không được kết nối trong phiên này.</span>
      </div>
      <div id="live-paused-overlay" class="paused-overlay" style="display:none">
        ⏸ Đã tạm dừng
        <span>Nhấn "Tiếp tục" để tiếp tục phiên</span>
      </div>
      <div class="live-camera-overlay"></div>
    </div>
    <div style="padding:14px 16px;background:#fff;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
      <div>
        <div class="eyebrow" style="margin-bottom:2px">THỜI GIAN PHIÊN</div>
        <div class="session-clock-large" id="live-clock">00:00</div>
      </div>
      <div class="session-controls">
        <button class="btn secondary" id="btn-pause-resume">
          <span id="pause-label">⏸ Tạm dừng</span>
        </button>
        <button class="btn danger" id="btn-leave-session">Rời phiên</button>
      </div>
    </div>
  </div>

  <!-- Info panel -->
  <div class="live-info-panel">
    <!-- Student info -->
    <div class="card pad">
      <div class="eyebrow" style="margin-bottom:10px">THÔNG TIN CỦA BẠN</div>
      <div class="student-cell" style="margin-bottom:12px">
        <div class="mini-avatar" style="width:40px;height:40px;font-size:13px">${esc(initials(user.name))}</div>
        <div>
          <div class="student-name">${esc(user.name)}</div>
          <div class="student-id">${esc(user.id)}</div>
        </div>
      </div>
      <div class="status-row"><span>Trạng thái</span>${badge('Đang tham gia', 'b-green')}</div>
      <div class="status-row"><span>Lớp</span><strong>${esc(c ? c.name : '—')}</strong></div>
      <div class="status-row"><span>Phiên</span><strong>${esc(s.type)}</strong></div>
    </div>

    <!-- Events panel -->
    <div class="card pad">
      <div class="row between" style="margin-bottom:10px">
        <div class="eyebrow">SỰ KIỆN ĐÃ GHI NHẬN</div>
        <span id="events-count" class="badge b-grey">${events.length}</span>
      </div>
      <div class="events-scroll" id="events-list">
        ${renderEventsList(events)}
      </div>
      <p class="footer-note" style="margin-top:8px">
        Sự kiện chuyển tab được ghi nhận tự động bằng Page Visibility API. Đây là thông tin hỗ trợ, không phải kết luận vi phạm.
      </p>
    </div>

    <!-- Notice -->
    <div class="notice warn">
      <span>⚠</span>
      <span>${s.type === 'Phiên thi'
        ? 'Bạn đang trong phiên thi. Tránh rời khỏi trang hoặc chuyển tab để không ảnh hưởng đến kết quả.'
        : 'Hãy duy trì sự tập trung trong suốt phiên học.'}</span>
    </div>
  </div>
</div>`;

  return renderShell(content, 'student-home');
}

export function initStudentLive(params = {}) {
  const sessionId = params.sessionId || getParam('sessionId');
  const courseId  = params.courseId  || getParam('courseId');
  const user      = getCurrentUser();

  _sessionId = sessionId;
  _paused    = false;

  // Join session in mock DB
  if (user && sessionId) {
    studentJoinSession(sessionId, user.id, user.name);
    addManualEvent(sessionId, 'joined', 'Tham gia phiên', 'Sinh viên đã vào phiên học.');
  }

  // Attach camera stream if available from prepare page
  const liveVideo  = document.getElementById('live-video');
  const camHolder  = document.getElementById('live-camera-placeholder');
  _liveStream = window.__edufocus_camera_stream || null;

  if (_liveStream && _liveStream.active && liveVideo) {
    attachToVideo(_liveStream, liveVideo);
    liveVideo.style.display = 'block';
    if (camHolder) camHolder.style.display = 'none';
    window.__edufocus_camera_stream = null; // consume it
  }

  // Start timer
  const clockEl = document.getElementById('live-clock');
  _timerId = startTimer(sessionId, (elapsed, formatted) => {
    if (clockEl) clockEl.textContent = formatted;
  });

  // Visibility tracking
  _cleanupVis = initVisibilityTracking(sessionId);

  // Update events when visibility changes
  document.addEventListener('visibilitychange', updateEventsList);

  // Pause / Resume
  const pauseBtn   = document.getElementById('btn-pause-resume');
  const pauseLabel = document.getElementById('pause-label');
  const pauseOverlay = document.getElementById('live-paused-overlay');

  if (pauseBtn) {
    pauseBtn.addEventListener('click', () => {
      if (_paused) {
        // Resume
        _paused = false;
        resumeTimer(sessionId, (elapsed, formatted) => {
          if (clockEl) clockEl.textContent = formatted;
        });
        if (pauseLabel)   pauseLabel.textContent = '⏸ Tạm dừng';
        if (pauseOverlay) pauseOverlay.style.display = 'none';
        addManualEvent(sessionId, 'resumed', 'Tiếp tục phiên', 'Đã tiếp tục phiên học.');
        updateEventsList();
      } else {
        // Pause
        _paused = true;
        pauseTimer(sessionId);
        if (pauseLabel)   pauseLabel.textContent = '▶ Tiếp tục';
        if (pauseOverlay) pauseOverlay.style.display = 'flex';
        addManualEvent(sessionId, 'paused', 'Tạm dừng phiên', 'Sinh viên đã tạm dừng phiên học.');
        updateEventsList();
      }
    });
  }

  // Leave session
  const leaveBtn = document.getElementById('btn-leave-session');
  if (leaveBtn) {
    leaveBtn.addEventListener('click', () => showLeaveModal(sessionId, courseId));
  }

  // Cleanup on navigate away
  window.__edufocus_live_cleanup = () => cleanupLivePage(sessionId);
}

function updateEventsList() {
  const events  = getSessionEvents(_sessionId);
  const listEl  = document.getElementById('events-list');
  const countEl = document.getElementById('events-count');
  if (listEl)  listEl.innerHTML = renderEventsList(events);
  if (countEl) countEl.textContent = events.length;
  if (listEl)  listEl.scrollTop = listEl.scrollHeight;
}

function renderEventsList(events) {
  if (!events.length) {
    return `<div style="color:var(--muted);font-size:12px;text-align:center;padding:16px">Chưa có sự kiện nào được ghi nhận.</div>`;
  }
  return events.slice().reverse().map(e => `
<div class="event-item">
  <span class="event-time">${e.displayTime || ''}</span>
  <div>
    <div class="event-label">${esc(e.label || e.type)}</div>
    <div style="font-size:11px;color:var(--muted)">${esc(e.description || '')}</div>
  </div>
</div>`).join('');
}

function showLeaveModal(sessionId, courseId) {
  const modalRoot = document.getElementById('modal-root');
  modalRoot.innerHTML = `
<div class="overlay" id="leave-overlay">
  <div class="modal" role="dialog" aria-modal="true" onclick="event.stopPropagation()">
    <h3>Rời phiên học?</h3>
    <p>Bạn sẽ rời khỏi phiên học hiện tại. Thời gian và sự kiện đã được ghi nhận. Bạn có thể quay lại nếu phiên vẫn đang diễn ra.</p>
    <div class="modal-actions">
      <button class="btn secondary" id="cancel-leave">Ở lại phiên</button>
      <button class="btn danger" id="confirm-leave">Rời phiên</button>
    </div>
  </div>
</div>`;

  document.getElementById('leave-overlay').addEventListener('click', e => {
    if (e.target.id === 'leave-overlay') modalRoot.innerHTML = '';
  });
  document.getElementById('cancel-leave').addEventListener('click', () => modalRoot.innerHTML = '');
  document.getElementById('confirm-leave').addEventListener('click', () => {
    addManualEvent(sessionId, 'left', 'Rời phiên', 'Sinh viên đã rời khỏi phiên học.');
    cleanupLivePage(sessionId);
    modalRoot.innerHTML = '';
    toast('Đã rời phiên học.');
    navigate('student-home');
  });
}

function cleanupLivePage(sessionId) {
  // Stop timer
  if (sessionId) stopTimer(sessionId);
  _paused = false;

  // Stop visibility tracking
  if (_cleanupVis) { _cleanupVis(); _cleanupVis = null; }
  document.removeEventListener('visibilitychange', updateEventsList);

  // Stop camera
  if (_liveStream) {
    _liveStream.getTracks().forEach(t => t.stop());
    _liveStream = null;
  }
  stopCurrentCamera();
}

