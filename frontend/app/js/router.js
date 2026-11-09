/**
 * EduFocus — SPA Router
 */

import { getCurrentUser } from './auth.js';
import { stopCurrentCamera } from './camera.js';

const TEACHER_ROUTES = new Set([
  'teacher-home', 'teacher-course', 'teacher-session', 'teacher-student', 'teacher-reports'
]);
const STUDENT_ROUTES = new Set([
  'student-home', 'student-course', 'student-prepare', 'student-live', 'student-history', 'student-summary'
]);
const PUBLIC_ROUTES  = new Set(['login', 'register', 'forgot']);

let _currentRoute  = 'login';
let _currentParams = {};
let _renderFn      = null;  // set by main.js

export function initRouter(renderCallback) {
  _renderFn = renderCallback;
  // Restore from sessionStorage
  try {
    const saved = JSON.parse(sessionStorage.getItem('edufocus-route') || '{}');
    if (saved.route) {
      _currentRoute  = saved.route;
      _currentParams = saved.params || {};
    }
  } catch (e) {}
}

export function navigate(route, params = {}) {
  const user = getCurrentUser();

  // Public routes: anyone can access
  if (PUBLIC_ROUTES.has(route)) {
    _currentRoute  = route;
    _currentParams = params;
    _saveRoute();
    _renderFn && _renderFn(route, params);
    window.scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }

  // Must be logged in
  if (!user) {
    _currentRoute  = 'login';
    _currentParams = {};
    _saveRoute();
    _renderFn && _renderFn('login', {});
    return;
  }

  // Role guards
  if (TEACHER_ROUTES.has(route) && user.role !== 'teacher') {
    import('./ui.js').then(({ toast }) => toast('Khu vực này dành cho giảng viên.'));
    return;
  }
  if (STUDENT_ROUTES.has(route) && user.role !== 'student') {
    import('./ui.js').then(({ toast }) => toast('Khu vực này dành cho sinh viên.'));
    return;
  }

  // Stop camera when leaving camera-related pages
  const leavingCamera = !['student-prepare', 'student-live'].includes(route);
  if (leavingCamera) {
    stopCurrentCamera();
  }

  _currentRoute  = route;
  _currentParams = params;
  _saveRoute();
  _renderFn && _renderFn(route, params);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

export function getCurrentRoute() {
  return { route: _currentRoute, params: _currentParams };
}

export function getParam(key) {
  return _currentParams[key] ?? null;
}

function _saveRoute() {
  try {
    sessionStorage.setItem('edufocus-route', JSON.stringify({
      route:  _currentRoute,
      params: _currentParams
    }));
  } catch (e) {}
}

