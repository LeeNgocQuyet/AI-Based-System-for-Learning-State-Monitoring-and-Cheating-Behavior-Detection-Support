/**
 * EduFocus — Teacher Course Detail Page
 */

import { renderShell } from './shell.js';
import { getCourse, getSessions, getActiveSession, getRoster, createSession } from '../data.js';
import { esc, badge, btn, toast, initials } from '../ui.js';
import { recentSessionsTable } from './teacher-home.js';
import { navigate, getParam } from '../router.js';

let _openSessionModal = null;

export function renderTeacherCourse(params = {}) {
  const courseId = params.courseId || getParam('courseId');
  const c = getCourse(courseId);
  if (!c) {
    return renderShell(`<div class="empty"><h3>Không tìm thấy lớp học phần.</h3>
      ${btn('Quay lại', 'teacher-home', 'secondary')}</div>`, 'teacher-home');
  }

  const s         = getActiveSession(c.id);
  const sessions  = getSessions(c.id).sort((a, b) => b.startedAt.localeCompare(a.startedAt));
  const joined    = s ? s.participants.filter(p => p.status !== 'absent').length : 0;

  const content = `
<div class="breadcrumb">
  <button class="link-btn" data-route="teacher-home">Lớp học phần</button> / ${esc(c.code)}
</div>
<div class="page-head">
  <div>
    <div class="eyebrow">LỚP HỌC PHẦN</div>
    <h1 class="h1">${esc(c.name)}</h1>
    <p class="sub">${esc(c.code)} · ${c.studentCount} sinh viên</p>
  </div>
  <div class="toolbar">
    ${s
      ? btn('Xem dashboard phiên', 'view-session', 'primary', `data-id="${esc(s.id)}"`)
      : btn('＋ Mở phiên học / thi', 'open-session-modal', 'primary', `data-id="${esc(c.id)}"`)
    }
  </div>
</div>

<div class="grid grid-3" style="margin-bottom:16px">
  <div class="card metric">
    <div class="value">${c.studentCount}</div>
    <div class="label">Sĩ số lớp</div>
    <div class="hint">Danh sách sinh viên được ghi danh</div>
  </div>
  <div class="card metric">
    <div class="value">${sessions.length}</div>
    <div class="label">Phiên đã tổ chức</div>
    <div class="hint">Học tập và kiểm tra</div>
  </div>
  <div class="card metric">
    <div class="value">${s ? joined : 0}</div>
    <div class="label">Đã tham gia phiên hiện tại</div>
    <div class="hint">${s ? 'Cập nhật khi sinh viên vào lớp' : 'Chưa có phiên đang diễn ra'}</div>
  </div>
</div>

${s ? '' : `
<div class="card pad" style="margin-bottom:16px">
  <div class="row between wrap">
    <div>
      <h2 class="section-title">Chưa có phiên đang diễn ra</h2>
      <p class="section-sub">Mở phiên học hoặc phiên thi để sinh viên trong lớp nhận được thông báo và tham gia.</p>
    </div>
    ${btn('Mở phiên học / thi', 'open-session-modal', 'primary', `data-id="${esc(c.id)}"`)}
  </div>
  <div class="notice info" style="margin-top:15px">Sau khi mở phiên, thông báo sẽ xuất hiện ở trang chủ của sinh viên đã đăng ký lớp này.</div>
</div>`
}

<div class="card pad">
  <div class="row between">
    <div>
      <h2 class="section-title">Lịch sử phiên của lớp</h2>
      <p class="section-sub">Xem các phiên học và phiên thi đã kết thúc.</p>
    </div>
    ${badge(sessions.length + ' phiên', 'b-grey')}
  </div>
  ${recentSessionsTable(sessions)}
</div>`;

  return renderShell(content, 'teacher-home');
}

export function initTeacherCourse() {
  // handled by main.js event delegation
}

/* ---- Open Session Modal ---- */
export function showOpenSessionModal(courseId) {
  const c = getCourse(courseId);
  if (!c) return;

  const modalRoot = document.getElementById('modal-root');
  modalRoot.innerHTML = `
<div class="overlay" id="session-modal-overlay">
  <div class="modal" role="dialog" aria-modal="true" onclick="event.stopPropagation()">
    <h3>Mở phiên mới cho lớp ${esc(c.name)}</h3>
    <p>Chọn loại phiên và nhập thông tin cơ bản.</p>
    <div class="field">
      <label>Loại phiên</label>
      <div class="session-type">
        <button class="session-choice selected" data-session-type="Phiên học" id="type-study">
          <strong>📚 Phiên học</strong>
          <span>Học tập, thảo luận, bài giảng thông thường</span>
        </button>
        <button class="session-choice" data-session-type="Phiên thi" id="type-exam">
          <strong>📝 Phiên thi</strong>
          <span>Kiểm tra, thi cử, đánh giá</span>
        </button>
      </div>
    </div>
    <div class="field">
      <label for="session-title">Tên phiên</label>
      <input class="input" id="session-title" placeholder="VD: Bài giảng tuần 10 — Nguyên tắc UX" value="">
    </div>
    <div class="field">
      <label for="session-duration">Thời lượng (phút)</label>
      <input class="input" type="number" id="session-duration" value="90" min="10" max="360">
    </div>
    <div id="session-modal-error" class="notice danger-note hidden" style="margin-bottom:10px">Vui lòng nhập tên phiên.</div>
    <div class="modal-actions">
      <button class="btn secondary" data-action="close-modal">Hủy</button>
      <button class="btn primary" id="confirm-open-session" data-course-id="${esc(courseId)}">Mở phiên ngay</button>
    </div>
  </div>
</div>`;

  let selectedType = 'Phiên học';

  // Type toggle
  modalRoot.querySelectorAll('[data-session-type]').forEach(btn => {
    btn.addEventListener('click', () => {
      modalRoot.querySelectorAll('[data-session-type]').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      selectedType = btn.dataset.sessionType;
    });
  });

  // Overlay close
  document.getElementById('session-modal-overlay').addEventListener('click', (e) => {
    if (e.target.id === 'session-modal-overlay') modalRoot.innerHTML = '';
  });

  // Confirm
  document.getElementById('confirm-open-session').addEventListener('click', () => {
    const title    = document.getElementById('session-title').value.trim();
    const duration = parseInt(document.getElementById('session-duration').value) || 90;
    const errEl    = document.getElementById('session-modal-error');
    if (!title) { errEl.classList.remove('hidden'); return; }
    errEl.classList.add('hidden');

    const session = createSession(courseId, selectedType, title, duration);
    modalRoot.innerHTML = '';
    toast('Đã mở phiên: ' + title);
    navigate('teacher-session', { sessionId: session.id });
  });
}

