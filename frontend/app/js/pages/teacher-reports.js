/**
 * EduFocus — Teacher Reports Page
 */

import { renderShell } from './shell.js';
import { getSessions, getCourses, getCourse } from '../data.js';
import { getCurrentUser } from '../auth.js';
import { esc, badge, btn, formatDate } from '../ui.js';

export function renderTeacherReports() {
  const user     = getCurrentUser();
  const sessions = getSessions().sort((a, b) => b.startedAt.localeCompare(a.startedAt));
  const courses  = getCourses(user.id);

  const totalStudents = courses.reduce((a, c) => a + c.studentCount, 0);
  const finished      = sessions.filter(s => s.status === 'Đã kết thúc');
  const totalJoined   = finished.reduce((a, s) => a + (s.participants || []).filter(p => p.status !== 'absent').length, 0);
  const totalEvents   = finished.reduce((a, s) => a + (s.events || []).length, 0);

  const content = `
<div class="page-head">
  <div>
    <div class="eyebrow">BÁO CÁO</div>
    <h1 class="h1">Tổng quan phiên học</h1>
    <p class="sub">Lịch sử tất cả các phiên học và phiên thi trên các lớp bạn phụ trách.</p>
  </div>
</div>

<div class="grid grid-4" style="margin-bottom:24px">
  <div class="card metric">
    <div class="value">${sessions.length}</div>
    <div class="label">Tổng số phiên</div>
    <div class="hint">Cả đang diễn ra và đã kết thúc</div>
  </div>
  <div class="card metric">
    <div class="value">${finished.length}</div>
    <div class="label">Phiên đã hoàn thành</div>
    <div class="hint">Dữ liệu có thể phân tích</div>
  </div>
  <div class="card metric">
    <div class="value">${totalJoined}</div>
    <div class="label">Lượt tham gia</div>
    <div class="hint">Từ tất cả phiên đã kết thúc</div>
  </div>
  <div class="card metric">
    <div class="value">${totalEvents}</div>
    <div class="label">Sự kiện đã ghi nhận</div>
    <div class="hint">Từ dữ liệu minh họa</div>
  </div>
</div>

<div class="card pad">
  <div class="row between" style="margin-bottom:16px">
    <div>
      <h2 class="section-title">Danh sách tất cả phiên</h2>
      <p class="section-sub">Xem chi tiết từng phiên bằng cách nhấn vào nút dashboard.</p>
    </div>
    ${badge(sessions.length + ' phiên', 'b-grey')}
  </div>

  ${sessions.length
    ? `<div class="table-wrap">
        <table class="table">
          <thead><tr>
            <th>Phiên</th><th>Lớp học phần</th><th>Loại</th>
            <th>Bắt đầu</th><th>Thời lượng</th><th>Đã tham gia</th><th>Trạng thái</th><th></th>
          </tr></thead>
          <tbody>
            ${sessions.map(s => {
              const c    = getCourse(s.courseId);
              const pLen = (s.participants || []).filter(p => p.status !== 'absent').length;
              const tot  = (s.participants || []).length;
              return `
<tr>
  <td><strong>${esc(s.title)}</strong><div class="student-id">${esc(s.id)}</div></td>
  <td>${esc(c ? c.name : s.courseId)}</td>
  <td>${s.type === 'Phiên thi' ? badge('Thi', 'b-purple') : badge('Học', 'b-blue')}</td>
  <td>${s.startedLabel || formatDate(s.startedAt)}</td>
  <td>${s.duration} phút</td>
  <td>${pLen}/${tot || '—'}</td>
  <td>${badge(s.status, s.status === 'Đang diễn ra' ? 'b-green' : 'b-grey')}</td>
  <td><button class="link-btn" data-action="view-session" data-id="${esc(s.id)}">Xem dashboard →</button></td>
</tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>`
    : `<div class="empty"><h3>Chưa có phiên nào</h3><p>Mở một phiên học hoặc phiên thi để bắt đầu ghi dữ liệu.</p></div>`}
</div>

<div class="notice info" style="margin-top:18px">
  ⓘ Dữ liệu tham gia và sự kiện trong báo cáo này là dữ liệu minh họa. Hệ thống thực tế sẽ tổng hợp từ backend sau khi tích hợp.
</div>`;

  return renderShell(content, 'teacher-reports');
}

