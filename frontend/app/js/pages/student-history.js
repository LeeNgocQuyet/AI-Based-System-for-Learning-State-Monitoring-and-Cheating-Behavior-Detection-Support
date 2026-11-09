/**
 * EduFocus — Student History Page
 */

import { renderShell } from './shell.js';
import { getStudentSessions, getStudentCourses, getCourse } from '../data.js';
import { getCurrentUser } from '../auth.js';
import { esc, badge, btn, formatDate } from '../ui.js';

export function renderStudentHistory() {
  const user     = getCurrentUser();
  const sessions = getStudentSessions(user.id).sort((a, b) => b.startedAt.localeCompare(a.startedAt));

  const content = `
<div class="page-head">
  <div>
    <div class="eyebrow">LỊCH SỬ CỦA TÔI</div>
    <h1 class="h1">Lịch sử phiên tham gia</h1>
    <p class="sub">Danh sách các phiên học và phiên thi bạn đã tham gia.</p>
  </div>
</div>

<div class="card pad">
  ${sessions.length
    ? `<div class="table-wrap">
        <table class="table">
          <thead><tr>
            <th>Phiên</th><th>Lớp học phần</th><th>Loại</th>
            <th>Thời gian</th><th>Trạng thái</th><th>Của tôi</th>
          </tr></thead>
          <tbody>
            ${sessions.map(s => {
              const c    = getCourse(s.courseId);
              const myP  = (s.participants || []).find(p => p.studentId === user.id);
              return `
<tr>
  <td><strong>${esc(s.title)}</strong><div class="student-id">${esc(s.id)}</div></td>
  <td>${esc(c ? c.name : s.courseId)}</td>
  <td>${s.type === 'Phiên thi' ? badge('Thi', 'b-purple') : badge('Học', 'b-blue')}</td>
  <td>${s.startedLabel || formatDate(s.startedAt)}</td>
  <td>${badge(s.status, s.status === 'Đang diễn ra' ? 'b-green' : 'b-grey')}</td>
  <td>${myP
    ? `<span class="status-chip ${statusCls(myP.status)}">${statusLabel(myP.status)}</span>`
    : badge('Không rõ', 'b-grey')}</td>
</tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>`
    : `<div class="empty">
        <h3>Chưa có phiên nào</h3>
        <p>Các phiên học và phiên thi bạn tham gia sẽ xuất hiện tại đây.</p>
        ${btn('Về trang chủ', 'student-home', 'primary')}
      </div>`}
</div>

<div class="notice info" style="margin-top:18px">
  ⓘ Lịch sử này dựa trên dữ liệu mock trong bản demo. Sau khi tích hợp backend, dữ liệu sẽ được lấy từ máy chủ.
</div>`;

  return renderShell(content, 'student-history');
}

function statusCls(s)   { return { stable:'status-stable', attention:'status-attention', technical:'status-technical', absent:'status-absent' }[s] || 'status-absent'; }
function statusLabel(s) { return { stable:'Ổn định', attention:'Cần xem xét', technical:'Lỗi thiết bị', absent:'Chưa tham gia' }[s] || '—'; }

