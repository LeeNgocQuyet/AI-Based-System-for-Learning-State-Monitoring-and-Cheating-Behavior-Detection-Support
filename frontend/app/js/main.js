/**
 * EduFocus — Main Entry Point
 * SPA router, event delegation, page lifecycle management.
 *
 * Event delegation is set up ONCE at document level (boot) to prevent
 * duplicate listeners accumulating on each page render.
 */

import { initRouter, navigate, getCurrentRoute, getParam } from './router.js';
import { getCurrentUser, logout } from './auth.js';
import { toast } from './ui.js';
import { getCourse, getSession, seedAttendance, getData as _getData } from './data.js';
import { stopCurrentCamera } from './camera.js';

// Pages
import { renderLogin,          initLogin }          from './pages/login.js';
import { renderRegister,       initRegister }        from './pages/register.js';
import { renderForgot,         initForgot }          from './pages/forgot.js';
import { renderTeacherHome,    initTeacherHome }     from './pages/teacher-home.js';
import { renderTeacherCourse,  initTeacherCourse }   from './pages/teacher-course.js';
import { renderTeacherSession, setRosterFilter, setRosterQuery, toggleCameraWall,
         resetRosterFilter, showEndSessionModal, rosterRows }   from './pages/teacher-session.js';
import { renderTeacherStudent, toggleStudentFeed }   from './pages/teacher-student.js';
import { renderTeacherReports }                      from './pages/teacher-reports.js';
import { renderStudentHome }                         from './pages/student-home.js';
import { renderStudentCourse }                       from './pages/student-course.js';
import { renderStudentPrepare, initStudentPrepare }  from './pages/student-prepare.js';
import { renderStudentLive,    initStudentLive }      from './pages/student-live.js';
import { renderStudentHistory }                      from './pages/student-history.js';
import { showOpenSessionModal }                      from './pages/teacher-course.js';

const app = document.getElementById('app');

// ---- RENDER ----
function renderPage(route, params = {}) {
  // Cleanup previous page
  if (window.__edufocus_live_cleanup)    { window.__edufocus_live_cleanup();    window.__edufocus_live_cleanup    = null; }
  if (window.__edufocus_prepare_cleanup) { window.__edufocus_prepare_cleanup(); window.__edufocus_prepare_cleanup = null; }

  // Expose DB for template functions
  window.__edufocus_db = _getData();

  let html = '';
  switch (route) {
    case 'login':            html = renderLogin();            break;
    case 'register':         html = renderRegister();         break;
    case 'forgot':           html = renderForgot();           break;
    case 'teacher-home':     html = renderTeacherHome();      break;
    case 'teacher-course':   html = renderTeacherCourse(params);  break;
    case 'teacher-session':  html = renderTeacherSession(params); break;
    case 'teacher-student':  html = renderTeacherStudent(params); break;
    case 'teacher-reports':  html = renderTeacherReports();   break;
    case 'student-home':     html = renderStudentHome();      break;
    case 'student-course':   html = renderStudentCourse(params);  break;
    case 'student-prepare':  html = renderStudentPrepare(params); break;
    case 'student-live':     html = renderStudentLive(params);    break;
    case 'student-history':  html = renderStudentHistory();   break;
    default:
      html = `<div class="auth-wrap"><div class="card auth-card"><h1>404</h1><p>Trang không tồn tại.</p></div></div>`;
  }

  app.innerHTML = html;

  // Init page-specific JS
  switch (route) {
    case 'login':           initLogin();                   break;
    case 'register':        initRegister();                break;
    case 'forgot':          initForgot();                  break;
    case 'teacher-home':    initTeacherHome();             break;
    case 'teacher-course':  initTeacherCourse();           break;
    case 'student-prepare': initStudentPrepare(params);    break;
    case 'student-live':    initStudentLive(params);       break;
  }
}

// ---- EVENT DELEGATION (registered ONCE at boot) ----
// Handles clicks anywhere in the document via event bubbling.
// Using document-level delegation means no duplicate listeners on re-render.

function handleClick(e) {
  const tgt = e.target.closest('[data-action], [data-route], [data-roster-filter]');
  if (!tgt) return;

  if (tgt.dataset.rosterFilter) {
    const { route, params } = getCurrentRoute();
    setRosterFilter(tgt.dataset.rosterFilter);
    renderPage(route, params);
    return;
  }

  if (tgt.dataset.route) {
    e.preventDefault();
    navigate(tgt.dataset.route);
    return;
  }

  const action     = tgt.dataset.action;
  const id         = tgt.dataset.id;
  const sessionId  = tgt.dataset.session || tgt.dataset.id;
  const courseId   = tgt.dataset.course;
  const studentId  = tgt.dataset.student;
  const eventIdx   = tgt.dataset.eventIndex;

  switch (action) {
    // ---- Auth ----
    case 'logout':
      logout();
      stopCurrentCamera();
      sessionStorage.removeItem('edufocus-route');
      navigate('login');
      break;

    case 'reset-demo':
      import('./data.js').then(({ resetData }) => {
        resetData();
        sessionStorage.clear();
        toast('Đã đặt lại dữ liệu demo.');
      });
      break;

    // ---- Navigation ----
    case 'teacher-home':
    case 'teacher-reports':
      navigate(action);
      break;

    case 'open-course':
      navigate('teacher-course', { courseId: id });
      break;

    case 'open-student-course':
      navigate('student-course', { courseId: id });
      break;

    case 'view-session': {
      const s = getSession(sessionId);
      if (!s) { toast('Không tìm thấy phiên.'); return; }
      navigate('teacher-session', { sessionId: s.id });
      break;
    }

    case 'view-student':
      navigate('teacher-student', { sessionId, studentId });
      break;

    // ---- Session actions ----
    case 'open-session-modal':
      showOpenSessionModal(id);
      break;

    case 'open-course-session':
      showOpenSessionModal(id);
      break;

    case 'seed-attendance': {
      const s = getSession(sessionId);
      if (!s || s.attendanceSeeded) { toast('Dữ liệu đã được tạo.'); return; }
      seedAttendance(sessionId);
      toast('Đã tạo dữ liệu điểm danh minh họa!');
      const { route, params } = getCurrentRoute();
      renderPage(route, params);
      break;
    }

    case 'confirm-end-session':
      showEndSessionModal(sessionId);
      break;

    case 'close-modal':
    case 'overlay-close':
      document.getElementById('modal-root').innerHTML = '';
      break;

    // ---- Student actions ----
    case 'join-session':
    case 'go-prepare':
      navigate('student-prepare', { sessionId, courseId: courseId || id });
      break;

    case 'toggle-camera-wall': {
      toggleCameraWall();
      const { route, params } = getCurrentRoute();
      renderPage(route, params);
      break;
    }

    case 'toggle-student-feed': {
      toggleStudentFeed();
      const { route, params } = getCurrentRoute();
      renderPage(route, params);
      break;
    }

    case 'reset-roster-filter': {
      resetRosterFilter();
      const { route, params } = getCurrentRoute();
      renderPage(route, params);
      break;
    }

    case 'view-snapshot':
      openSnapshotModal(studentId, sessionId, eventIdx);
      break;

    case 'open-class-report':
      navigate('teacher-session', { sessionId });
      break;
  }
}

function handleInput(e) {
  if (e.target.id === 'roster-search') {
    setRosterQuery(e.target.value);
    const { params } = getCurrentRoute();
    const s = getSession(params.sessionId);
    const c = s ? getCourse(s.courseId) : null;
    const rosterEl = document.getElementById('roster-table');
    if (rosterEl && s) rosterEl.innerHTML = rosterRows(s, c);
  }
}

function openSnapshotModal(studentId, sessionId, eventIndex) {
  import('./data.js').then(({ getSession, getCourse }) => {
    import('./pages/mock-camera.js').then(({ mockCameraFrame }) => {
      import('./ui.js').then(({ esc, badge, initials }) => {
        const s = getSession(sessionId);
        const p = s && s.participants ? s.participants.find(x => x.studentId === studentId) : null;
        const e = p && p.events ? p.events[Number(eventIndex)] : null;
        const c = s ? getCourse(s.courseId) : null;

        if (!s || !p) { toast('Không tìm thấy ảnh minh họa.'); return; }

        const modalRoot = document.getElementById('modal-root');
        modalRoot.innerHTML = `
<div class="overlay" id="snapshot-overlay">
  <div class="modal modal-evidence" role="dialog" aria-modal="true" onclick="event.stopPropagation()">
    <div class="modal-evidence-head">
      <div>
        <span class="eyebrow">MINH CHỨNG SỰ KIỆN · DEMO</span>
        <h3>${esc(e ? e.type : 'Sự kiện')}</h3>
        <p>${esc(p.studentName)} · ${esc(e && e.time ? new Date(e.time).toLocaleTimeString('vi-VN') : '')} · ${esc(c ? c.name : '')}</p>
      </div>
      <button class="icon-close" data-action="close-modal" aria-label="Đóng">×</button>
    </div>
    <div class="snapshot-modal-frame">${mockCameraFrame(p.studentName, 'attention', Number(eventIndex), 'snapshot')}</div>
    <div class="notice info" style="margin-top:16px">
      ${esc(e ? (e.description || 'Đây là hình ảnh mô phỏng được tạo cho bản demo UI/UX, không phải dữ liệu camera thực.') : '')}
    </div>
    <div class="modal-actions">
      <button class="btn secondary" data-action="close-modal">Đóng</button>
      <button class="btn primary" data-action="view-student" data-student="${esc(p.studentId)}" data-session="${esc(s.id)}">Mở hồ sơ sinh viên</button>
    </div>
  </div>
</div>`;

        document.getElementById('snapshot-overlay').addEventListener('click', ev => {
          if (ev.target.id === 'snapshot-overlay') modalRoot.innerHTML = '';
        });
      });
    });
  });
}

// ---- BOOT ----
function boot() {
  const user = getCurrentUser();
  let startRoute = 'login';
  let startParams = {};

  // Restore previous route for authenticated users
  if (user) {
    try {
      const saved = JSON.parse(sessionStorage.getItem('edufocus-route') || '{}');
      if (saved.route) {
        startRoute  = saved.route;
        startParams = saved.params || {};
      } else {
        startRoute = user.role === 'teacher' ? 'teacher-home' : 'student-home';
      }
    } catch (e) {
      startRoute = user.role === 'teacher' ? 'teacher-home' : 'student-home';
    }
  }

  // Single top-level event delegation — set up ONCE, never duplicated
  document.addEventListener('click', handleClick);
  document.addEventListener('input', handleInput);

  initRouter((route, params) => renderPage(route, params));
  renderPage(startRoute, startParams);
}

boot();
