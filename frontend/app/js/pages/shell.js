/**
 * EduFocus — Shared Shell (topbar + sidebar) helper
 * Used by all authenticated pages.
 */

import { getCurrentUser } from '../auth.js';
import { getCourses, getActiveSession } from '../data.js';
import { esc, initials } from '../ui.js';

export function renderShell(contentHTML, activeRoute = '') {
  const user    = getCurrentUser();
  if (!user) return contentHTML;

  const isTeacher = user.role === 'teacher';
  const courses   = isTeacher ? getCourses(user.id) : getCourses();

  /* ---- Top navigation items ---- */
  const navItems = isTeacher
    ? [
        ['teacher-home',    svgGrid(),   'Tổng quan'],
        ['teacher-reports', svgChart(),  'Báo cáo'],
      ]
    : [
        ['student-home',    svgHome(),   'Trang chủ'],
        ['student-history', svgClock(),  'Lịch sử của tôi'],
      ];

  /* ---- Course list in sidebar ---- */
  const courseAction = isTeacher ? 'open-course' : 'open-student-course';
  const courseLinks  = courses.map(c => {
    const active = getActiveSession(c.id);
    return `
<button class="nav" data-action="${courseAction}" data-id="${esc(c.id)}" title="${esc(c.name)}">
  <span class="nav-ico">${svgBook()}</span>
  <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">${esc(c.name)}</span>
  ${active ? '<span class="badge b-green" style="font-size:9px;padding:3px 6px;flex-shrink:0">LIVE</span>' : ''}
</button>`;
  }).join('');

  const sidebarItems = navItems.map(([route, icon, label]) =>
    `<button class="nav ${activeRoute === route ? 'active' : ''}" data-route="${route}">
      <span class="nav-ico">${icon}</span>${esc(label)}
    </button>`
  ).join('');

  return `
<header class="topbar">
  <div class="brand">
    <div class="brandmark">E</div>
    <span>EduFocus</span>
    <span class="brand-sub">Cổng học tập</span>
  </div>
  <div class="top-right">
    <span class="role-tag">${isTeacher ? 'Giảng viên' : 'Sinh viên'}</span>
    <div class="user-chip">
      <div class="avatar">${esc(initials(user.name))}</div>
      <span>${esc(user.name)}</span>
    </div>
    <button class="btn secondary btn-sm" data-action="logout">Đăng xuất</button>
  </div>
</header>
<div class="layout">
  <aside class="sidebar">
    <div class="side-label">KHÔNG GIAN LÀM VIỆC</div>
    ${sidebarItems}
    <div class="side-label" style="margin-top:22px">${isTeacher ? 'LỚP PHỤ TRÁCH' : 'LỚP ĐANG THEO HỌC'}</div>
    ${courseLinks}
    <div class="sidebar-foot">
      <strong>EduFocus</strong><br>
      Thông tin lớp và phiên trong bản demo dùng dữ liệu minh họa. Trạng thái quan sát không thay thế đánh giá của giảng viên.
    </div>
  </aside>
  <main class="main">${contentHTML}</main>
</div>`;
}

/* ---- SVG Icons ---- */
function svgGrid()  { return `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>`; }
function svgChart() { return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19V5M4 19H21"/><path d="m7 15 4-4 3 2 5-6"/></svg>`; }
function svgHome()  { return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 10 9-7 9 7"/><path d="M5 9v12h14V9M9 21v-7h6v7"/></svg>`; }
function svgClock() { return `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>`; }
function svgBook()  { return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21z"/><path d="M4 5.5v13A2.5 2.5 0 0 1 6.5 16H20"/></svg>`; }

