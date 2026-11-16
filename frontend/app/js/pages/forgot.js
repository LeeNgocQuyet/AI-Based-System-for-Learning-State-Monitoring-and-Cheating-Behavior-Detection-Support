/**
 * EduFocus — Forgot Password Page
 */

export function renderForgot() {
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
    <div class="eyebrow">KHÔI PHỤC TÀI KHOẢN</div>
    <h1>Quên mật khẩu?</h1>
    <p class="sub">Nhập email để nhận hướng dẫn đặt lại mật khẩu.</p>
    <form id="forgot-form" novalidate>
      <div class="field">
        <label for="forgot-email">Email</label>
        <input class="input" type="email" id="forgot-email" required placeholder="you@example.com" autocomplete="email">
      </div>
      <div id="forgot-error"  class="notice danger-note hidden" style="margin-bottom:10px">Vui lòng nhập email hợp lệ.</div>
      <div id="forgot-result" class="notice good hidden" style="margin-top:12px">
        Đã tiếp nhận yêu cầu. Nếu email phù hợp, hướng dẫn đặt lại mật khẩu sẽ được gửi trong vài phút.
      </div>
      <button class="btn primary" style="width:100%" type="submit">Gửi hướng dẫn</button>
    </form>
    <div class="auth-links" style="margin-top:14px">
      <button class="link-btn" data-route="login">← Đăng nhập</button>
    </div>
  </div>
</div>`;
}

export function initForgot() {
  const form = document.getElementById('forgot-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const email  = document.getElementById('forgot-email').value.trim();
    const errEl  = document.getElementById('forgot-error');
    const succEl = document.getElementById('forgot-result');

    errEl.classList.add('hidden');
    succEl.classList.add('hidden');

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errEl.classList.remove('hidden');
      return;
    }

    succEl.classList.remove('hidden');
    document.getElementById('forgot-email').value = '';
  });
}

