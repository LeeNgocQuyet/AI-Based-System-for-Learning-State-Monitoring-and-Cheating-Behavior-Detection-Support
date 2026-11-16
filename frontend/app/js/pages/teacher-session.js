/**
 * EduFocus — Teacher Session Dashboard
 */

import { renderShell } from './shell.js';
import { getSession, getCourse, updateSession, seedAttendance, getRoster } from '../data.js';
import { esc, badge, btn, toast, initials } from '../ui.js';
import { navigate, getParam } from '../router.js';
import { mockCameraFrame, cameraTile } from './mock-camera.js';

let _rosterFilter = 'all';
let _rosterQuery  = '';
let _cameraExpanded = false;

export function renderTeacherSession(params = {}) {
  const sessionId = params.sessionId || getParam('sessionId');
  const s = getSession(sessionId);

  if (!s) {
    return renderShell(`<div class="empty"><h3>Không tìm thấy phiên.</h3>
      ${btn('Quay lại', 'teacher-home', 'secondary')}</div>`, 'teacher-home');
  }

  const c = getCourse(s.courseId);

  if (s.status !== 'Đang diễn ra') {
    // Finished session view
    return renderFinishedSession(s, c);
  }

  return renderActiveSession(s, c);
}

function renderActiveSession(s, c) {
  const st = statsFor(s);
  const pct = x => st.total ? (x / st.total * 100).toFixed(1) : 0;
  const participants = [...(s.participants || [])];
  const prioritized  = participants.sort((a, b) => {
    const ord = { attention: 0, stable: 1, technical: 2, absent: 3 };
    return (ord[a.status] ?? 4) - (ord[b.status] ?? 4);
  });
  const visible = _cameraExpanded ? prioritized : prioritized.slice(0, 8);
  const connected = participants.filter(p => p.status === 'stable' || p.status === 'attention').length;

  const content = `
<div class="breadcrumb">
  <button class="link-btn" data-action="open-course" data-id="${esc(s.courseId)}">${esc(c ? c.name : s.courseId)}</button> / Dashboard phiên
</div>

<div class="card pad" style="margin-bottom:15px">
  <div class="row between wrap">
    <div>
      <div class="row wrap" style="gap:8px">
        ${badge(s.type === 'Phiên thi' ? 'PHIÊN THI' : 'PHIÊN HỌC', s.type === 'Phiên thi' ? 'b-purple' : 'b-green')}
        ${badge('Đang diễn ra', 'b-green')}
      </div>
      <h2 class="section-title" style="font-size:19px;margin-top:8px">${esc(s.title)}</h2>
      <p class="section-sub">Mã phiên ${esc(s.id)} · Bắt đầu ${esc(s.startedLabel)} · Thời lượng dự kiến ${s.duration} phút</p>
    </div>
    <div class="toolbar">
      ${btn('Mô phỏng điểm danh', 'seed-attendance', 'secondary', `data-id="${esc(s.id)}" ${s.attendanceSeeded ? 'disabled' : ''}`)}
      ${btn('Kết thúc phiên', 'confirm-end-session', 'danger', `data-id="${esc(s.id)}"`)}
    </div>
  </div>
  <div class="notice info" style="margin-top:14px">
    Các trạng thái và hình ảnh trong dashboard là dữ liệu minh họa. "Cần xem lại" là tín hiệu để kiểm tra ngữ cảnh, không phải kết luận sinh viên mất tập trung hay vi phạm.
  </div>
</div>

<div class="grid grid-5" style="margin-bottom:18px">
  <div class="card metric"><div class="value">${st.total}</div><div class="label">Sĩ số lớp</div></div>
  <div class="card metric"><div class="value" style="color:var(--primary)">${st.joined}</div><div class="label">Đã tham gia</div></div>
  <div class="card metric"><div class="value" style="color:var(--primary)">${st.stable}</div><div class="label">Tín hiệu ổn định</div></div>
  <div class="card metric"><div class="value" style="color:var(--amber)">${st.attention}</div><div class="label">Cần xem xét</div></div>
  <div class="card metric"><div class="value" style="color:var(--red)">${st.technical + st.absent}</div><div class="label">Lỗi / chưa vào</div></div>
</div>

<!-- Camera Wall -->
<section class="card pad camera-wall-section">
  <div class="section-heading-row">
    <div>
      <div class="eyebrow">THEO DÕI LỚP HỌC</div>
      <h2 class="section-title">Camera toàn lớp</h2>
      <p class="section-sub">Tổng quan trạng thái kết nối của ${participants.length} sinh viên trong phiên.</p>
    </div>
    <div class="camera-wall-summary">
      <strong>${connected}/${participants.length}</strong>
      <span>camera mô phỏng kết nối</span>
    </div>
  </div>
  <div class="camera-wall-toolbar">
    <div class="camera-legend">
      <span><i class="legend-dot connected"></i>Đang kết nối</span>
      <span><i class="legend-dot warning"></i>Cần xem lại</span>
      <span><i class="legend-dot offline"></i>Ngoại tuyến</span>
    </div>
    <span class="demo-disclosure">ⓘ Luồng hình ảnh được mô phỏng cho demo UI/UX</span>
  </div>
  <div class="camera-wall-grid" id="camera-wall-grid">
    ${visible.length ? visible.map((p, i) => cameraTile(p, s.id, i)).join('') : emptyAttendance()}
  </div>
  ${participants.length > 8 ? `
  <div class="camera-wall-actions">
    <span class="muted small">${_cameraExpanded ? 'Đang hiển thị toàn bộ lớp' : `Đang xem ${visible.length}/${prioritized.length} sinh viên`}</span>
    <button class="btn secondary btn-sm" data-action="toggle-camera-wall">
      ${_cameraExpanded ? 'Thu gọn danh sách' : 'Xem toàn bộ ' + prioritized.length + ' sinh viên'}
    </button>
  </div>` : ''}
</section>

<!-- Evidence Gallery -->
${renderEvidenceGallery(s)}

<!-- Bottom split -->
<div class="split" style="margin-top:18px">
  <div class="card pad">
    <div class="row between">
      <div>
        <h2 class="section-title">Tình hình tham gia của cả lớp</h2>
        <p class="section-sub">Theo dõi sĩ số và trạng thái từng sinh viên.</p>
      </div>
      <span class="small muted">${st.joined}/${st.total} đã tham gia</span>
    </div>
    <div class="progress-track" style="margin-top:18px">
      <span style="width:${pct(st.stable)}%;background:#6b967c"></span>
      <span style="width:${pct(st.attention)}%;background:#d7a458"></span>
      <span style="width:${pct(st.technical)}%;background:#c9766d"></span>
      <span style="width:${pct(st.absent)}%;background:#dce2dc"></span>
    </div>
    <div class="progress-legend">
      <span><i class="stat-dot" style="background:#6b967c"></i>Ổn định (${st.stable})</span>
      <span><i class="stat-dot" style="background:#d7a458"></i>Cần xem xét (${st.attention})</span>
      <span><i class="stat-dot" style="background:#c9766d"></i>Lỗi thiết bị (${st.technical})</span>
      <span><i class="stat-dot" style="background:#dce2dc"></i>Chưa tham gia (${st.absent})</span>
    </div>
    <div class="divider"></div>
    <div class="row between">
      <h3 class="section-title">Danh sách sinh viên</h3>
      ${badge('Nhấn vào tên để xem chi tiết', 'b-grey')}
    </div>
    <div class="roster-toolbar">
      <input class="input" id="roster-search" value="${esc(_rosterQuery)}" placeholder="Tìm tên hoặc mã sinh viên">
      <div class="filter-tabs">
        ${[['all','Tất cả'],['stable','Ổn định'],['attention','Cần xem xét'],['technical','Lỗi thiết bị'],['absent','Chưa tham gia']]
          .map(([v,l]) => `<button class="filter-tab ${_rosterFilter===v?'active':''}" data-roster-filter="${v}">${l}</button>`).join('')}
      </div>
    </div>
    <div id="roster-table">${rosterRows(s, c)}</div>
  </div>

  <div class="card pad">
    <div class="row between">
      <div>
        <h2 class="section-title">Những bạn cần xem lại</h2>
        <p class="section-sub">Danh sách rút gọn để giảng viên kiểm tra.</p>
      </div>
      ${badge(String(st.attention + st.technical), 'b-amber')}
    </div>
    ${attentionList(s)}
    <div class="divider"></div>
    <h3 class="section-title">Thông tin phiên</h3>
    <div class="status-row"><span>Loại phiên</span><strong>${esc(s.type)}</strong></div>
    <div class="status-row"><span>Thời gian bắt đầu</span><strong>${esc(s.startedLabel)}</strong></div>
    <div class="status-row"><span>Trạng thái</span>${badge('Đang diễn ra', 'b-green')}</div>
    <div class="status-row"><span>Mã lớp</span><strong>${esc(c ? c.id : '—')}</strong></div>
  </div>
</div>`;

  return renderShell(content, 'teacher-home');
}

function renderFinishedSession(s, c) {
  const st = statsFor(s);
  const content = `
<div class="breadcrumb">
  <button class="link-btn" data-action="open-course" data-id="${esc(s.courseId)}">${esc(c ? c.name : s.courseId)}</button> / Chi tiết phiên
</div>
<div class="page-head">
  <div>
    <div class="eyebrow">CHI TIẾT PHIÊN</div>
    <h1 class="h1">${esc(s.title)}</h1>
    <p class="sub">${esc(c ? c.name : '')} · ${esc(s.type)} · ${esc(s.startedLabel)}</p>
  </div>
  ${btn('Quay lại lớp', 'open-course', 'secondary', `data-id="${esc(s.courseId)}"`)}
</div>
<div class="grid grid-4" style="margin-bottom:16px">
  <div class="card metric"><div class="value">${st.total}</div><div class="label">Sĩ số lớp</div></div>
  <div class="card metric"><div class="value">${st.joined}</div><div class="label">Đã tham gia</div></div>
  <div class="card metric"><div class="value">${st.attention}</div><div class="label">Cần xem xét</div></div>
  <div class="card metric"><div class="value">${st.technical}</div><div class="label">Lỗi thiết bị</div></div>
</div>
<div class="grid grid-2">
  <div class="card pad"><h2 class="section-title">Danh sách sinh viên</h2>${rosterRows(s, c)}</div>
  <div class="card pad">
    <h2 class="section-title">Sự kiện của phiên</h2>
    ${s.events && s.events.length
      ? `<div class="signal-timeline">${s.events.map(e => `
          <article>
            <h4>${esc(e.time ? new Date(e.time).toLocaleTimeString('vi-VN') : '')} · ${esc(e.type)}</h4>
            <p>${esc(e.description)}</p>
          </article>`).join('')}
         </div>`
      : `<div class="empty"><h3>Chưa có sự kiện</h3></div>`}
  </div>
</div>`;
  return renderShell(content, 'teacher-home');
}

function emptyAttendance() {
  return `<div class="empty" style="grid-column:1/-1">
    <h3>Chưa có sinh viên tham gia</h3>
    <p>Nhấn "Mô phỏng điểm danh" để xem dữ liệu minh họa.</p>
  </div>`;
}

function renderEvidenceGallery(s) {
  const items = (s.participants || [])
    .flatMap(p => (p.events || [])
      .filter(e => /Nhắm mắt|Nhìn lệch|Cúi|Rời khỏi/i.test(e.type))
      .map(e => ({ p, e })))
    .slice(0, 6);

  return `
<section class="card pad evidence-section">
  <div class="section-heading-row">
    <div>
      <div class="eyebrow">MINH CHỨNG SỰ KIỆN</div>
      <h2 class="section-title">Ảnh chụp cần xem lại</h2>
      <p class="section-sub">Ảnh chụp minh họa gắn với các tín hiệu cần giảng viên kiểm tra thêm.</p>
    </div>
    ${badge(items.length + ' ảnh minh họa', 'b-amber')}
  </div>
  ${items.length
    ? `<div class="snapshot-grid">${items.map(({ p, e }, i) => snapshotCard(p, e, s.id, i)).join('')}</div>`
    : `<div class="empty evidence-empty"><h3>Chưa có ảnh chụp cần xem lại</h3><p>Thử tạo dữ liệu điểm danh minh họa để xem các tình huống mẫu.</p></div>`}
  <p class="evidence-footnote">Ảnh trong bản demo là khung hình giao diện dựng sẵn, không phải ảnh thật được ghi từ webcam sinh viên.</p>
</section>`;
}

function snapshotCard(p, e, sessionId, index) {
  return `
<article class="snapshot-card">
  <button class="snapshot-preview" data-action="view-snapshot"
    data-student="${esc(p.studentId)}" data-session="${esc(sessionId)}" data-event-index="${index}">
    ${mockCameraFrame(p.studentName, 'attention', index, 'snapshot')}
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
</article>`;
}

export function rosterRows(s, c) {
  const q   = _rosterQuery.toLowerCase();
  const all = (s.participants || []).filter(p =>
    (_rosterFilter === 'all' || p.status === _rosterFilter) &&
    (!q || p.studentName.toLowerCase().includes(q) || p.studentId.toLowerCase().includes(q))
  );

  if (!all.length) {
    return `<div class="empty"><h3>Không có sinh viên phù hợp</h3><p>Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm.</p>
      <button class="link-btn" data-action="reset-roster-filter">Xóa bộ lọc</button></div>`;
  }

  return `
<div class="table-wrap">
  <table class="table" style="min-width:580px">
    <thead><tr>
      <th>Sinh viên</th><th>Trạng thái</th><th>Tham gia lúc</th><th>Tín hiệu gần nhất</th><th></th>
    </tr></thead>
    <tbody>
      ${all.map(p => `
      <tr>
        <td><div class="student-cell">
          <div class="mini-avatar">${esc(initials(p.studentName))}</div>
          <div>
            <div class="student-name">${esc(p.studentName)}</div>
            <div class="student-id">${esc(p.studentId)}</div>
          </div>
        </div></td>
        <td><span class="status-chip ${statusCls(p.status)}">${statusLabel(p.status)}</span></td>
        <td>${p.joinedAt ? new Date(p.joinedAt).toLocaleTimeString('vi-VN') : '—'}</td>
        <td>${esc(p.events && p.events.length ? p.events[p.events.length-1].type : 'Chưa có tín hiệu')}</td>
        <td><button class="link-btn" data-action="view-student" data-student="${esc(p.studentId)}" data-session="${esc(s.id)}">Chi tiết</button></td>
      </tr>`).join('')}
    </tbody>
  </table>
</div>`;
}

function attentionList(s) {
  const arr = (s.participants || []).filter(p => p.status === 'attention' || p.status === 'technical').slice(0, 8);
  if (!arr.length) {
    return `<div class="empty" style="padding:25px 5px"><h3>Chưa có trường hợp cần xem lại</h3><p>Danh sách sẽ cập nhật khi có tín hiệu hoặc lỗi thiết bị.</p></div>`;
  }
  return `<div class="list-stack" style="margin-top:12px">
    ${arr.map(p => `
    <div class="list-item">
      <div class="student-cell">
        <div class="mini-avatar">${esc(initials(p.studentName))}</div>
        <div>
          <div class="student-name">${esc(p.studentName)}</div>
          <div class="student-id">${esc(p.events && p.events.length ? p.events[p.events.length-1].type : 'Cần chú ý')}</div>
        </div>
      </div>
      <button class="link-btn" data-action="view-student" data-student="${esc(p.studentId)}" data-session="${esc(s.id)}">Xem</button>
    </div>`).join('')}
  </div>`;
}

function statsFor(s) {
  const p = s.participants || [];
  return {
    total:     p.length,
    joined:    p.filter(x => x.status !== 'absent').length,
    stable:    p.filter(x => x.status === 'stable').length,
    attention: p.filter(x => x.status === 'attention').length,
    technical: p.filter(x => x.status === 'technical').length,
    absent:    p.filter(x => x.status === 'absent').length,
  };
}

function statusCls(s)   { return { stable:'status-stable', attention:'status-attention', technical:'status-technical', absent:'status-absent' }[s] || 'status-absent'; }
function statusLabel(s) { return { stable:'Ổn định', attention:'Cần xem xét', technical:'Lỗi thiết bị', absent:'Chưa tham gia' }[s] || '—'; }

export function setRosterFilter(f) { _rosterFilter = f; }
export function setRosterQuery(q)  { _rosterQuery  = q; }
export function toggleCameraWall() { _cameraExpanded = !_cameraExpanded; }
export function resetRosterFilter(){ _rosterFilter = 'all'; _rosterQuery = ''; }

/* ---- End Session Modal ---- */
export function showEndSessionModal(sessionId) {
  const modalRoot = document.getElementById('modal-root');
  modalRoot.innerHTML = `
<div class="overlay" id="end-session-overlay">
  <div class="modal" role="dialog" aria-modal="true" onclick="event.stopPropagation()">
    <h3>Kết thúc phiên?</h3>
    <p>Phiên sẽ được đánh dấu là đã kết thúc. Sinh viên không thể tiếp tục tham gia. Hành động này không thể hoàn tác.</p>
    <div class="modal-actions">
      <button class="btn secondary" data-action="close-modal">Hủy</button>
      <button class="btn danger" id="confirm-end-btn">Kết thúc phiên</button>
    </div>
  </div>
</div>`;

  document.getElementById('end-session-overlay').addEventListener('click', e => {
    if (e.target.id === 'end-session-overlay') modalRoot.innerHTML = '';
  });

  document.getElementById('confirm-end-btn').addEventListener('click', () => {
    updateSession(sessionId, { status: 'Đã kết thúc' });
    modalRoot.innerHTML = '';
    toast('Phiên đã được kết thúc.');
    navigate('teacher-home');
  });
}

