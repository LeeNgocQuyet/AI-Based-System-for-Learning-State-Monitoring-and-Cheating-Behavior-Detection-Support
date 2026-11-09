/**
 * EduFocus — Student Home Page
 */

import { renderShell } from './shell.js';
import { getStudentCourses, getActiveSession } from '../data.js';
import { getCurrentUser } from '../auth.js';
import { esc, badge, btn, initials } from '../ui.js';
import { navigate } from '../router.js';

export function renderStudentHome() {
  const user    = getCurrentUser();
  const courses = getStudentCourses(user.id);

  // Find any active session in enrolled courses
  const activeSessions = courses
    .map(c => ({ course: c, session: getActiveSession(c.id) }))
    .filter(x => x.session);

  const colors = { C001: '#6d8f7d', C002: '#8c9bba', C003: '#c69a69', C004: '#b07e82' };

  const content = `
<div class="page-head">
  <div>
    <div class="eyebrow">TRANG CHỦ SINH VIÊN</div>
    <h1 class="h1">Chào ${esc(user.name)} 👋</h1>
    <p class="sub">Xem các lớp học phần đang theo học và tham gia phiên nếu có thông báo.</p>
  </div>
</div>

<!-- Active sessions banner -->
${activeSessions.length ? `
<div class="card pad" style="margin-bottom:18px;border-left:4px solid var(--primary)">
  <div class="eyebrow" style="margin-bottom:8px">PHIÊN ĐANG DIỄN RA</div>
  <div class="grid" style="gap:10px">
    ${activeSessions.map(({ course, session }) => `
    <div class="live-banner">
      <div>
        <strong>${esc(session.title)}</strong>
        <p>${esc(course.name)} · ${esc(session.type)} · ${session.duration} phút</p>
      </div>
      ${btn('Vào phiên ngay', 'join-session', 'primary', `data-session="${esc(session.id)}" data-course="${esc(course.id)}"`)}
    </div>`).join('')}
  </div>
</div>` : ''}

<!-- Course list -->
<div class="row between wrap" style="margin-bottom:12px">
  <div>
    <h2 class="section-title">Lớp học phần của tôi</h2>
    <p class="section-sub">Nhấn vào lớp để xem thông tin chi tiết và lịch sử phiên.</p>
  </div>
  ${badge(courses.length + ' lớp đang theo học', 'b-green')}
</div>

${courses.length
  ? `<div class="grid grid-2">
      ${courses.map(c => {
        const s     = getActiveSession(c.id);
        const color = colors[c.id] || '#6d8f7d';
        return `
<article class="card course-card">
  <div class="course-strip" style="background:${color}"></div>
  <div class="course-top">
    <div>
      <div class="course-code">${esc(c.code)}</div>
      <div class="course-name">${esc(c.name)}</div>
      <div class="course-meta">
        <span>${c.studentCount} sinh viên trong lớp</span>
      </div>
    </div>
    ${s ? badge('Đang có phiên', 'b-green') : badge('Không có phiên', 'b-grey')}
  </div>
  ${s
    ? `<div class="live-banner">
        <div>
          <strong>${esc(s.title)}</strong>
          <p>${esc(s.type)} · ${s.duration} phút</p>
        </div>
        ${btn('Vào phiên', 'join-session', 'soft', `data-session="${esc(s.id)}" data-course="${esc(c.id)}"`)}
       </div>`
    : `<div class="notice info"><span>ℹ</span><span>Hiện chưa có phiên học nào đang mở.</span></div>`}
  <div class="course-actions">
    ${btn('Xem lớp', 'open-student-course', 'secondary', `data-id="${esc(c.id)}"`)}
    ${s ? btn('Chuẩn bị tham gia', 'go-prepare', 'primary', `data-session="${esc(s.id)}" data-course="${esc(c.id)}"`) : ''}
  </div>
</article>`;
      }).join('')}
    </div>`
  : `<div class="empty card pad">
      <h3>Chưa có lớp học phần</h3>
      <p>Bạn chưa được đăng ký vào lớp nào. Liên hệ giảng viên để được thêm vào lớp.</p>
    </div>`}

<div class="card pad" style="margin-top:18px">
  <div class="row between">
    <div>
      <h2 class="section-title">Thông tin tài khoản</h2>
    </div>
  </div>
  <div class="status-row"><span>Họ tên</span><strong>${esc(user.name)}</strong></div>
  <div class="status-row"><span>Mã sinh viên</span><strong>${esc(user.id)}</strong></div>
  <div class="status-row"><span>Email</span><strong>${esc(user.email)}</strong></div>
  <div class="status-row"><span>Vai trò</span>${badge('Sinh viên', 'b-blue')}</div>
</div>`;

  return renderShell(content, 'student-home');
}

