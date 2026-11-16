/**
 * EduFocus — Register Page
 */

import { register } from '../auth.js';
import { navigate } from '../router.js';

export function renderRegister() {
  return `
<header class="topbar">
  <div class="brand">
    <div class="brandmark">E</div>
    <span>EduFocus</span>
  </div>
  <button class="btn secondary btn-sm" data-route="login">← Quay lại</button>
</header>
<div class="auth-wrap">
  <div class="card auth-card">
    <div class="eyebrow">TÀI KHOẢN SINH VIÊN</div>
    <h1>Tạo tài khoản</h1>
    <p class="sub">Tài khoản đăng ký công khai mặc định là sinh viên.</p>
    <form id="register-form" novalidate>
      <div class="field">
        <label for="reg-name">Họ và tên</label>
        <input id="reg-name" class="input" required placeholder="Nguyễn Văn A" autocomplete="name">
      </div>
      <div class="field">
        <label for="reg-email">Email</label>
        <input id="reg-email" class="input" type="email" required placeholder="you@example.com" autocomplete="email">
      </div>
      <div class="field">
        <label for="reg-pass">Mật khẩu</label>
        <input id="reg-pass" class="input" type="password" minlength="8" required placeholder="Tối thiểu 8 ký tự" autocomplete="new-password">
        <span class="field-hint">Tối thiểu 8 ký tự</span>
      </div>
      <div class="field">
        <label for="reg-confirm">Nhập lại mật khẩu</label>
        <input id="reg-confirm" class="input" type="password" required placeholder="Nhập lại mật khẩu" autocomplete="new-password">
      </div>
      <div id="reg-error"   class="notice danger-note hidden" style="margin-bottom:10px"></div>
      <div id="reg-success" class="notice good hidden" style="margin-bottom:10px">Tạo tài khoản thành công! Đang chuyển đến trang đăng nhập…</div>
      <button class="btn primary" style="width:100%" type="submit">Tạo tài khoản sinh viên</button>
    </form>
    <p class="footer-note" style="margin-top:14px">Giảng viên được cấp tài khoản từ hệ thống, không tự đăng ký vai trò giảng viên.</p>
  </div>
</div>`;
}

export function initRegister() {
  const form = document.getElementById('register-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const name     = document.getElementById('reg-name').value.trim();
    const email    = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-pass').value;
    const confirm  = document.getElementById('reg-confirm').value;
    const errEl    = document.getElementById('reg-error');
    const succEl   = document.getElementById('reg-success');

    errEl.classList.add('hidden');
    succEl.classList.add('hidden');

    if (password !== confirm) {
      errEl.textContent = 'Mật khẩu xác nhận không khớp.';
      errEl.classList.remove('hidden');
      return;
    }

    const result = register(name, email, password);
    if (result.success) {
      succEl.classList.remove('hidden');
      setTimeout(() => navigate('login'), 1800);
    } else {
      errEl.textContent = result.error || 'Đã xảy ra lỗi, vui lòng thử lại.';
      errEl.classList.remove('hidden');
    }
  });
}

