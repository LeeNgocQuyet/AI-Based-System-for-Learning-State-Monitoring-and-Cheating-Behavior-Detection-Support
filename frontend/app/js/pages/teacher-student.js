/**
 * EduFocus — Teacher Student Detail Page
 */

import { renderShell } from './shell.js';
import { getSession, getCourse } from '../data.js';
import { esc, badge, btn, initials } from '../ui.js';
import { navigate, getParam } from '../router.js';
import { mockCameraFrame } from './mock-camera.js';

let _feedPaused = false;

export function renderTeacherStudent(params = {}) {
  const sessionId = params.sessionId || getParam('sessionId');
  const studentId = params.studentId || getParam('studentId');
  const s = getSession(sessionId);
  const p = s && s.participants ? s.participants.find(x => x.studentId === studentId) : null;
  const c = s ? getCourse(s.courseId) : null;

  if (!s || !p) {
    return renderShell(`
<div class="empty">
  <h3>Không tìm thấy thông tin sinh viên</h3>
  ${btn('Quay lại', 'teacher-home', 'secondary')}
</div>`, 'teacher-home');
  }

  const feedAvailable = p.status === 'stable' || p.status === 'attention';
  const events        = p.events || [];

  const content = `
<div class="breadcrumb">
  <button class="link-btn" data-action="view-session" data-id="${esc(s.id)}">${esc(c ? c.name : s.courseId)} · Dashboard phiên</button> / Chi tiết sinh viên
</div>
<div class="page-head">
  <div>
    <div class="eyebrow">CHI TIẾT SINH VIÊN</div>
    <h1 class="h1">${esc(p.studentName)}</h1>
    <p class="sub">${esc(p.studentId)} · ${esc(c ? c.name : '')} · ${esc(s.title)}</p>
  </div>
  ${btn('Quay lại dashboard lớp', 'view-session', 'secondary', `data-id="${esc(s.id)}"`)}
</div>

<div class="grid grid-3" style="margin-bottom:18px">
  <div class="card metric">
    <div class="value"><span class="status-chip ${statusCls(p.status)}">${statusLabel(p.status)}</span></div>
    <div class="label">Trạng thái hiện tại</div>
  </div>
  <div class="card metric">
    <div class="value" style="font-size:18px">${p.joinedAt ? new Date(p.joinedAt).toLocaleTimeString('vi-VN') : '—'}</div>
    <div class="label">Thời điểm tham gia</div>
  </div>
  <div class="card metric">
    <div class="value">${events.length}</div>
    <div class="label">Sự kiện trong phiên</div>
  </div>
</div>

<!-- Student Live Monitor -->
<section class="card pad student-live-monitor">
  <div class="section-heading-row">
    <div>
      <div class="eyebrow">CAMERA CÁ NHÂN</div>
      <h2 class="section-title">Theo dõi camera sinh viên</h2>
      <p class="section-sub">Khung xem trực tiếp được mô phỏng trong prototype.</p>
    </div>
    ${badge(_feedPaused ? 'Đã tạm dừng xem' : 'LIVE · MÔ PHỎNG', _feedPaused ? 'b-grey' : 'b-green')}
  </div>
  <div class="student-monitor-layout">
    <div class="student-live-frame ${_feedPaused ? 'feed-paused' : ''}">
      ${_feedPaused
        ? `<div class="feed-paused-state"><strong>Đã tạm dừng khung xem</strong><span>Nhấn tiếp tục để xem mô phỏng.</span></div>`
        : mockCameraFrame(p.studentName, p.status, 2, 'live')}
    </div>
    <div class="student-monitor-meta">
      <div class="monitor-person">
        <div class="mini-avatar">${esc(initials(p.studentName))}</div>
        <div>
          <strong>${esc(p.studentName)}</strong>
          <small>${esc(p.studentId)}</small>
        </div>
      </div>
      <div class="status-row"><span>Tình trạng camera</span><strong>${feedAvailable ? 'Đang kết nối (demo)' : p.status === 'technical' ? 'Gián đoạn' : 'Chưa tham gia'}</strong></div>
      <div class="status-row"><span>Trạng thái phiên</span><span class="status-chip ${statusCls(p.status)}">${statusLabel(p.status)}</span></div>
      <div class="status-row"><span>Lần cập nhật mô phỏng</span><strong>Vừa cập nhật</strong></div>
      <button class="btn ${_feedPaused ? 'primary' : 'secondary'}" data-action="toggle-student-feed" style="width:100%;margin-top:14px">
        ${_feedPaused ? 'Tiếp tục xem' : 'Tạm dừng xem'}
      </button>
      <small class="demo-disclosure block-disclosure">Prototype chỉ minh họa bố cục camera cá nhân. Không có luồng video thật từ thiết bị sinh viên.</small>
    </div>
  </div>
</section>

<div class="student-detail-lower">
  <!-- Evidence Gallery -->
  <section class="card pad">
    <div class="section-heading-row">
      <div>
        <div class="eyebrow">LỊCH SỬ HÌNH ẢNH</div>
        <h2 class="section-title">Ảnh chụp tại thời điểm có tín hiệu</h2>
        <p class="section-sub">Chọn một ảnh để xem khung hình và ngữ cảnh sự kiện.</p>
      </div>
      ${badge(events.filter(e => /Nhắm mắt|Nhìn lệch|Rời khỏi/i.test(e.type)).length + ' ảnh', 'b-amber')}
    </div>
    ${renderStudentEvidence(p, s)}
  </section>

  <!-- Signal Timeline -->
  <div class="card pad">
    <h2 class="section-title">Lịch sử tín hiệu</h2>
    ${events.length
      ? `<div class="signal-timeline" style="margin-top:14px">
          ${events.map(e => `
          <article>
            <h4>${esc(e.time ? new Date(e.time).toLocaleTimeString('vi-VN') : '')} · ${esc(e.type)}</h4>
            <p>${esc(e.description || e.type)}</p>
          </article>`).join('')}
         </div>`
      : `<div class="empty" style="padding:24px 5px"><h3>Chưa có tín hiệu</h3><p>Không có sự kiện nào được ghi nhận.</p></div>`}
  </div>
</div>`;

  return renderShell(content, 'teacher-home');
}

function renderStudentEvidence(p, s) {
  const items = (p.events || []).filter(e => /Nhắm mắt|Nhìn lệch|Rời khỏi/i.test(e.type));
  if (!items.length) {
    return `<div class="empty"><h3>Chưa có ảnh chụp</h3><p>Các ảnh chụp minh họa sẽ xuất hiện khi sinh viên có sự kiện được đánh dấu cần xem lại.</p></div>`;
  }
  return `<div class="snapshot-grid student-snapshot-grid">
    ${items.map((e, i) => `
    <article class="snapshot-card">
      <button class="snapshot-preview" data-action="view-snapshot"
        data-student="${esc(p.studentId)}" data-session="${esc(s.id)}" data-event-index="${i}">
        ${mockCameraFrame(p.studentName, 'attention', i, 'snapshot')}
        <span class="snapshot-open">⌕ Xem ảnh</span>
      </button>
      <div class="snapshot-content">
        <div class="row between wrap">
          <strong>${esc(e.type)}</strong>
          ${badge('Cần xem lại', 'b-amber')}
        </div>
        <p>${esc(p.studentName)} · ${esc(e.time ? new Date(e.time).toLocaleTimeString('vi-VN') : '')}</p>
        <small>${esc(e.description || 'Tín hiệu minh họa được ghi nhận trong phiên.')}</small>
      </div>
    </article>`).join('')}
  </div>`;
}

export function toggleStudentFeed() { _feedPaused = !_feedPaused; }

function statusCls(s)   { return { stable:'status-stable', attention:'status-attention', technical:'status-technical', absent:'status-absent' }[s] || 'status-absent'; }
function statusLabel(s) { return { stable:'Ổn định', attention:'Cần xem xét', technical:'Lỗi thiết bị', absent:'Chưa tham gia' }[s] || '—'; }

