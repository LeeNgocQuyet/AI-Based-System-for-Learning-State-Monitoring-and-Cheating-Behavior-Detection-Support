/**
 * EduFocus — Mock Camera Frame Builder
 * Used by teacher dashboard for student camera simulation.
 */

import { esc, initials } from '../ui.js';

export function mockCameraFrame(name, status, index = 0, variant = 'tile') {
  const offline  = status === 'technical' || status === 'absent';
  const labels   = {
    technical: 'Camera gián đoạn',
    absent:    'Chưa tham gia',
    attention: 'Tín hiệu cần xem lại',
    stable:    'Đang kết nối'
  };
  const chipText = offline
    ? 'CAMERA OFFLINE'
    : variant === 'snapshot' ? 'FRAME DEMO' : 'LIVE · DEMO';
  const timeText = variant === 'snapshot' ? 'ẢNH MINH HỌA' : '●';

  return `
<div class="mock-frame scene-${index % 4} ${offline ? 'is-offline' : ''} ${variant === 'snapshot' ? 'is-snapshot' : ''}">
  <div class="mock-frame-top">
    <span class="mock-camera-chip">${chipText}</span>
    <span class="mock-frame-time">${timeText}</span>
  </div>
  ${offline
    ? `<div class="mock-offline">
        <span class="mock-offline-icon">${status === 'technical' ? '⌁' : '◌'}</span>
        <strong>${labels[status] || 'Không có tín hiệu'}</strong>
        <small>Không có hình ảnh trong bản demo</small>
       </div>`
    : `<div class="mock-scene">
        <div class="mock-window"></div>
        <div class="mock-person">
          <div class="person-head"><span>${esc(initials(name))}</span></div>
          <div class="person-body"></div>
        </div>
        <div class="mock-desk"></div>
        <div class="mock-scan-box"></div>
       </div>
       <div class="mock-frame-bottom">
         <span>${esc(name)}</span>
         <span>${labels[status] || 'Đang kết nối'}</span>
       </div>`
  }
  <span class="mock-frame-watermark">EDUFOCUS · DEMO</span>
</div>`;
}

export function cameraTile(p, sessionId, index) {
  const joined = p.status !== 'absent' && p.status !== 'technical';
  return `
<article class="camera-tile ${p.status === 'attention' ? 'needs-review' : ''}">
  <button class="camera-tile-preview" type="button"
    data-action="view-student" data-student="${esc(p.studentId)}" data-session="${esc(sessionId)}"
    aria-label="Mở chi tiết ${esc(p.studentName)}">
    ${mockCameraFrame(p.studentName, p.status, index)}
  </button>
  <div class="camera-tile-info">
    <div class="camera-tile-person">
      <strong>${esc(p.studentName)}</strong>
      <small>${esc(p.studentId)}</small>
    </div>
    <span class="status-chip ${statusCls(p.status)}">${statusLabel(p.status)}</span>
  </div>
  <div class="camera-tile-foot">
    <span class="camera-connection ${joined ? 'is-connected' : ''}">
      <i></i>${joined ? 'Đã kết nối' : 'Ngoại tuyến'}
    </span>
    <button class="link-btn" data-action="view-student"
      data-student="${esc(p.studentId)}" data-session="${esc(sessionId)}">Chi tiết</button>
  </div>
</article>`;
}

function statusCls(s) {
  return { stable: 'status-stable', attention: 'status-attention', technical: 'status-technical', absent: 'status-absent' }[s] || 'status-absent';
}
function statusLabel(s) {
  return { stable: 'Ổn định', attention: 'Cần xem xét', technical: 'Lỗi thiết bị', absent: 'Chưa tham gia' }[s] || '—';
}

