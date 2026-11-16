/**
 * EduFocus — Login Page
 */

import { login } from '../auth.js';
import { navigate } from '../router.js';
import { resetData } from '../data.js';

export function renderLogin() {
  return `
<header class="topbar">
  <div class="brand">
    <div class="brandmark">E</div>
    <span>EduFocus</span>
    <span class="brand-sub">Cổng học tập</span>
  </div>
  <span class="role-tag">Bản demo tương tác</span>
</header>
<div class="auth-wrap">
  <div class="card auth-card">
    <div class="brand">
      <div class="brandmark">E</div>
      <span>EduFocus</span>
    </div>
    <h1>Chào mừng bạn quay lại</h1>
    <p class="sub">Đăng nhập để xem lớp học phần và các phiên đang diễn ra.</p>
    <form id="login-form" novalidate>
      <div class="field">
        <label for="login-email">Email</label>
        <input class="input" id="login-email" type="email" required placeholder="you@example.com" autocomplete="email">
      </div>
      <div class="field">
        <label for="login-password">Mật khẩu</label>
        <input class="input" id="login-password" type="password" required placeholder="Nhập mật khẩu" autocomplete="current-password">
      </div>
      <div id="login-error" class="notice danger-note hidden" style="margin-bottom:10px">
        Thông tin đăng nhập chưa đúng.
      </div>
      <button class="btn primary" style="width:100%;margin-top:8px" type="submit">Đăng nhập</button>
    </form>
    <div class="auth-links">
      <button class="link-btn" data-route="forgot">Quên mật khẩu?</button>
      <button class="link-btn" data-route="register">Đăng ký sinh viên</button>
    </div>
    <div class="demo-box">
      <strong>Tài khoản dùng thử</strong><br>
      Giảng viên: <b>teacher@demo.test</b> / 12345678<br>
      Sinh viên: <b>student@demo.test</b> / 12345678<br>
      <button type="button" class="link-btn" data-action="reset-demo" style="margin-top:4px">Đặt lại dữ liệu demo</button>
    </div>
    <p class="footer-note">Mẹo: đăng nhập giảng viên, mở một phiên cho lớp; sau đó đăng nhập sinh viên để thấy thông báo lớp đang diễn ra.</p>
  </div>
</div>`;
}

export function initLogin() {
  const form = document.getElementById('login-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const email    = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const errEl    = document.getElementById('login-error');

    errEl.classList.add('hidden');
    const result = login(email, password);

    if (result.success) {
      const user = result.user;
      navigate(user.role === 'teacher' ? 'teacher-home' : 'student-home');
    } else {
      errEl.textContent = result.error || 'Thông tin đăng nhập chưa đúng.';
      errEl.classList.remove('hidden');
    }
  });

  // Reset demo data button
  const resetBtn = document.querySelector('[data-action="reset-demo"]');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      resetData();
      sessionStorage.clear();
      import('../ui.js').then(({ toast }) => toast('Đã đặt lại dữ liệu demo.'));
    });
  }
}

