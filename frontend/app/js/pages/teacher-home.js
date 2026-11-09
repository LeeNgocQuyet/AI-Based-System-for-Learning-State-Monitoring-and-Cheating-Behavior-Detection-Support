/**
 * EduFocus — Teacher Home Page
 */

import { renderShell } from './shell.js';
import { getCourses, getSessions, getActiveSession } from '../data.js';
import { getCurrentUser } from '../auth.js';
import { esc, badge, btn, initials, formatDate } from '../ui.js';

export function renderTeacherHome() {
  const user     = getCurrentUser();
  const courses  = getCourses(user.id);
  const sessions = getSessions().sort((a, b) => b.startedAt.localeCompare(a.startedAt));
  const active   = sessions.filter(s => s.status === 'Đang diễn ra');
  const totalSv  = courses.reduce((a, c) => a + c.studentCount, 0);

  const content = `
<div class="page-head">
  <div>
    <div class="eyebrow">KHÔNG GIAN GIẢNG VIÊN</div>
    <h1 class="h1">Chào ${esc(user.name)}</h1>
    <p class="sub">Quản lý các lớp học phần, mở phiên học hoặc phiên thi và theo dõi tình hình tham gia của sinh viên.</p>
  </div>
  <div class="toolbar">
    ${btn('Xem báo cáo', 'teacher-reports', 'secondary')}
  </div>
</div>

<div class="grid grid-3" style="margin-bottom:18px">
  <div class="card metric">
    <div class="value">${courses.length}</div>
    <div class="label">Lớp học phần đang phụ trách</div>
    <div class="hint">Các lớp được phân công cho tài khoản này</div>
  </div>
  <div class="card metric">
    <div class="value">${active.length}</div>
    <div class="label">Phiên đang diễn ra</div>
    <div class="hint">Có thể xem điểm danh theo từng lớp</div>
  </div>
  <div class="card metric">
    <div class="value">${totalSv}</div>
    <div class="label">Tổng lượt sinh viên thuộc lớp</div>
    <div class="hint">Một sinh viên có thể học nhiều lớp</div>
  </div>
</div>

<div class="row between wrap" style="margin-bottom:12px">
  <div>
    <h2 class="section-title">Lớp học phần của tôi</h2>
    <p class="section-sub">Chọn một lớp để xem sĩ số, mở phiên và quản lý buổi học.</p>
  </div>
  ${badge(courses.length + ' lớp phụ trách', 'b-green')}
</div>
<div class="grid grid-2">
  ${courses.map(c => teacherCourseCard(c)).join('')}
</div>

<div class="card pad" style="margin-top:18px">
  <div class="row between">
    <div>
      <h2 class="section-title">Các phiên gần đây</h2>
      <p class="section-sub">Tổng hợp từ các lớp bạn phụ trách.</p>
    </div>
    <button class="link-btn" data-route="teacher-reports">Xem tất cả →</button>
  </div>
  ${recentSessionsTable(sessions.slice(0, 5))}
</div>`;

  return renderShell(content, 'teacher-home');
}

function teacherCourseCard(c) {
  const s      = getActiveSession(c.id);
  const joined = s ? s.participants.filter(p => p.status !== 'absent').length : 0;
  const colors = { C001: '#6d8f7d', C002: '#8c9bba', C003: '#c69a69', C004: '#b07e82' };
  const color  = colors[c.id] || '#6d8f7d';

  return `
<article class="card course-card">
  <div class="course-strip" style="background:${color}"></div>
  <div class="course-top">
    <div>
      <div class="course-code">${esc(c.code)} · ${esc(c.id)}</div>
      <div class="course-name">${esc(c.name)}</div>
      <div class="course-meta">
        <span>${c.studentCount} sinh viên</span>
      </div>
    </div>
    ${s ? badge('Đang mở phiên', 'b-green') : badge('Chưa mở phiên', 'b-grey')}
  </div>
  ${s
    ? `<div class="live-banner">
        <div>
          <strong>${s.type === 'Phiên thi' ? 'Phiên thi' : 'Phiên học'} đang diễn ra</strong>
          <p>${esc(s.title)} · ${joined}/${c.studentCount} đã tham gia</p>
        </div>
        ${btn('Mở dashboard', 'view-session', 'soft', `data-id="${esc(s.id)}"`)}
       </div>`
    : `<div class="notice info">
        <span>ℹ</span>
        <span>Chưa có phiên nào đang mở. Bạn có thể mở phiên học hoặc phiên thi để điểm danh.</span>
       </div>`
  }
  <div class="course-actions">
    ${btn('Mở lớp', 'open-course', 'secondary', `data-id="${esc(c.id)}"`)}
    ${s
      ? btn('Xem phiên', 'view-session', 'soft', `data-id="${esc(s.id)}"`)
      : btn('Mở phiên mới', 'open-session-modal', 'primary', `data-id="${esc(c.id)}"`)
    }
  </div>
</article>`;
}

export function recentSessionsTable(rows) {
  if (!rows.length) {
    return `<div class="empty"><h3>Chưa có phiên nào</h3><p>Các phiên bạn mở sẽ xuất hiện tại đây.</p></div>`;
  }
  const { getCourse } = window.__edufocus_data || {};
  return `
<div class="table-wrap" style="margin-top:12px">
  <table class="table">
    <thead><tr>
      <th>Phiên</th><th>Lớp học phần</th><th>Loại</th>
      <th>Bắt đầu</th><th>Đã tham gia</th><th>Trạng thái</th><th></th>
    </tr></thead>
    <tbody>
      ${rows.map(s => {
        const { getCourse: gc, getRoster } = window.__edufocus_data || {};
        const db   = window.__edufocus_db;
        const c    = db ? db.courses.find(c2 => c2.id === s.courseId) : null;
        const pLen = s.participants ? s.participants.filter(p => p.status !== 'absent').length : 0;
        const tot  = s.participants ? s.participants.length : '—';
        return `
<tr>
  <td><strong>${esc(s.title)}</strong><div class="student-id">${esc(s.id)}</div></td>
  <td>${esc(c ? c.name : s.courseId)}</td>
  <td>${s.type === 'Phiên thi' ? 'Thi' : 'Học tập'}</td>
  <td>${s.startedLabel || formatDate(s.startedAt)}</td>
  <td>${pLen}/${tot}</td>
  <td>${badge(s.status, s.status === 'Đang diễn ra' ? 'b-green' : 'b-grey')}</td>
  <td><button class="link-btn" data-action="view-session" data-id="${esc(s.id)}">Xem dashboard →</button></td>
</tr>`;
      }).join('')}
    </tbody>
  </table>
</div>`;
}

export function initTeacherHome() {
  // Event delegation handled by main.js
}

