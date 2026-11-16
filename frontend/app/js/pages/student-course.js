/**
 * EduFocus — Student Course Detail Page
 */

import { renderShell } from './shell.js';
import { getCourse, getSessions, getActiveSession } from '../data.js';
import { esc, badge, btn, formatDate } from '../ui.js';
import { navigate, getParam } from '../router.js';

export function renderStudentCourse(params = {}) {
  const courseId = params.courseId || getParam('courseId');
  const c = getCourse(courseId);
  if (!c) {
    return renderShell(`<div class="empty"><h3>Không tìm thấy lớp học phần.</h3>
      ${btn('Quay lại trang chủ', 'student-home', 'secondary')}</div>`, 'student-home');
  }

  const s       = getActiveSession(c.id);
  const history = getSessions(c.id).filter(s2 => s2.status === 'Đã kết thúc')
                                    .sort((a, b) => b.startedAt.localeCompare(a.startedAt));

  const content = `
<div class="breadcrumb">
  <button class="link-btn" data-route="student-home">Trang chủ</button> / ${esc(c.code)}
</div>
<div class="page-head">
  <div>
    <div class="eyebrow">LỚP HỌC PHẦN</div>
    <h1 class="h1">${esc(c.name)}</h1>
    <p class="sub">${esc(c.code)} · ${c.studentCount} sinh viên</p>
  </div>
  ${s ? btn('Tham gia phiên ngay', 'go-prepare', 'primary', `data-session="${esc(s.id)}" data-course="${esc(c.id)}"`) : ''}
</div>

${s ? `
<div class="card pad" style="margin-bottom:18px;border-left:4px solid var(--primary)">
  <div class="eyebrow" style="margin-bottom:6px">PHIÊN ĐANG DIỄN RA</div>
  <div class="live-banner" style="margin-top:0;border:0;padding:0;background:transparent">
    <div>
      <strong>${esc(s.title)}</strong>
      <p>${esc(s.type)} · ${s.duration} phút · ${s.participants ? s.participants.filter(p => p.status !== 'absent').length : 0} đã tham gia</p>
    </div>
    ${btn('Chuẩn bị & tham gia', 'go-prepare', 'primary', `data-session="${esc(s.id)}" data-course="${esc(c.id)}"`)}
  </div>
</div>` : `
<div class="notice info" style="margin-bottom:18px">
  <span>ℹ</span>
  <span>Hiện chưa có phiên học nào đang mở cho lớp này. Bạn sẽ nhận được thông báo khi giảng viên mở phiên.</span>
</div>`}

<div class="card pad">
  <div class="row between" style="margin-bottom:12px">
    <div>
      <h2 class="section-title">Lịch sử phiên của lớp</h2>
      <p class="section-sub">Các phiên học và phiên thi đã kết thúc.</p>
    </div>
    ${badge(history.length + ' phiên đã kết thúc', 'b-grey')}
  </div>
  ${history.length
    ? `<div class="table-wrap">
        <table class="table">
          <thead><tr><th>Phiên</th><th>Loại</th><th>Thời gian</th><th>Thời lượng</th><th>Trạng thái</th></tr></thead>
          <tbody>
            ${history.map(session => `
            <tr>
              <td><strong>${esc(session.title)}</strong><div class="student-id">${esc(session.id)}</div></td>
              <td>${session.type === 'Phiên thi' ? badge('Thi', 'b-purple') : badge('Học', 'b-blue')}</td>
              <td>${session.startedLabel || formatDate(session.startedAt)}</td>
              <td>${session.duration} phút</td>
              <td>${badge('Đã kết thúc', 'b-grey')}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>`
    : `<div class="empty"><h3>Chưa có phiên nào đã kết thúc</h3><p>Lịch sử sẽ hiển thị sau khi có phiên kết thúc.</p></div>`}
</div>`;

  return renderShell(content, 'student-home');
}

