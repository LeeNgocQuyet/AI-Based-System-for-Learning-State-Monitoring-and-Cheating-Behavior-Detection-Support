/**
 * EduFocus — Shared UI Helpers
 */

// ---- Toast ----
let _toastTimer = null;

export function toast(message, type = 'default', duration = 3200) {
  const root = document.getElementById('toast-root');
  if (!root) return;

  const el = document.createElement('div');
  el.className = `toast${type !== 'default' ? ` toast-${type}` : ''}`;
  el.textContent = message;
  root.appendChild(el);

  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(8px)';
    el.style.transition = 'opacity 0.25s, transform 0.25s';
    setTimeout(() => el.remove(), 280);
  }, duration);
}

export function toastSuccess(message) { toast(message, 'success'); }
export function toastError(message)   { toast(message, 'error'); }
export function toastWarning(message) { toast(message, 'warning'); }

// ---- Modal ----
export function showModal(title, body, actions = []) {
  return new Promise((resolve) => {
    const root = document.getElementById('modal-root');
    if (!root) { resolve(null); return; }

    const actionsHTML = actions.map((a, i) =>
      `<button class="btn ${a.cls || 'btn-ghost'}" data-modal-action="${i}">${esc(a.label)}</button>`
    ).join('');

    root.innerHTML = `
      <div class="modal-backdrop" id="modal-backdrop">
        <div class="modal" role="dialog" aria-modal="true">
          <div class="modal-header">
            <span class="modal-title">${esc(title)}</span>
            <button class="modal-close" data-modal-close>✕</button>
          </div>
          <div class="modal-body">${typeof body === 'string' ? body : ''}</div>
          ${actionsHTML ? `<div class="modal-footer">${actionsHTML}</div>` : ''}
        </div>
      </div>
    `;

    // Inject body element if it's a DOM node
    if (body instanceof HTMLElement) {
      root.querySelector('.modal-body').innerHTML = '';
      root.querySelector('.modal-body').appendChild(body);
    }

    function cleanup(value) {
      root.innerHTML = '';
      resolve(value);
    }

    root.querySelector('#modal-backdrop').addEventListener('click', (e) => {
      if (e.target.id === 'modal-backdrop') cleanup(null);
    });

    root.querySelectorAll('[data-modal-close]').forEach(btn => {
      btn.addEventListener('click', () => cleanup(null));
    });

    root.querySelectorAll('[data-modal-action]').forEach(btn => {
      const idx = parseInt(btn.dataset.modalAction);
      btn.addEventListener('click', () => {
        const action = actions[idx];
        cleanup(action ? (action.value !== undefined ? action.value : idx) : idx);
      });
    });
  });
}

export function closeModal() {
  const root = document.getElementById('modal-root');
  if (root) root.innerHTML = '';
}

// ---- String helpers ----

export function initials(name) {
  if (!name) return '?';
  return name.trim().split(/\s+/).map(w => w[0]).join('').toUpperCase().slice(0, 3);
}

export function esc(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ---- HTML builders ----

export function badge(label, cls = 'b-grey') {
  return `<span class="badge ${cls}">${esc(label)}</span>`;
}

export function btn(label, action, cls = 'secondary', extra = '') {
  return `<button class="btn ${cls}" data-action="${esc(action)}" ${extra}>${label}</button>`;
}

export function pageHead(eyebrow, title, sub, right = '') {
  return `<div class="page-head"><div><div class="eyebrow">${eyebrow}</div><h1 class="h1">${title}</h1><p class="sub">${esc(sub)}</p></div>${right ? `<div class="toolbar">${right}</div>` : ''}</div>`;
}

export function statusBadge(status) {
  const map = {
    'stable':       ['Ổn định',       'b-green'],
    'attention':    ['Cần xem xét',   'b-amber'],
    'technical':    ['Lỗi thiết bị',  'b-red'],
    'absent':       ['Chưa tham gia', 'b-grey'],
    'Đang diễn ra': ['Đang diễn ra',  'b-green'],
    'Đã kết thúc':  ['Đã kết thúc',   'b-grey'],
    'Phiên học':    ['Phiên học',     'b-blue'],
    'Phiên thi':    ['Phiên thi',     'b-purple'],
  };
  const [label, cls] = map[status] || [status, 'b-grey'];
  return badge(label, cls);
}

export function statusChip(status) {
  const map = {
    'stable':    ['Đang ổn định',   'status-stable'],
    'attention': ['Cần xem xét',    'status-attention'],
    'technical': ['Lỗi thiết bị',   'status-technical'],
    'absent':    ['Chưa tham gia',  'status-absent'],
  };
  const [label, cls] = map[status] || [status, 'status-absent'];
  return `<span class="status-chip ${cls}">${esc(label)}</span>`;
}

export function formatDate(date) {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return '';
  return d.toLocaleDateString('vi-VN', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

export function formatDateShort(date) {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return '';
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

export function timeAgo(date) {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Vừa xong';
  if (mins < 60) return `${mins} phút trước`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} giờ trước`;
  const days = Math.floor(hrs / 24);
  return `${days} ngày trước`;
}

// ---- Loading / empty states ----

export function loadingHTML() {
  return `<div class="empty-state"><div class="spinner"></div><p>Đang tải...</p></div>`;
}

export function emptyHTML(icon, title, desc = '') {
  return `
    <div class="empty-state">
      <div class="empty-icon">${icon}</div>
      <div class="empty-title">${esc(title)}</div>
      ${desc ? `<div class="empty-desc">${esc(desc)}</div>` : ''}
    </div>
  `;
}

// ---- DOM helpers ----

export function el(selector) {
  return document.querySelector(selector);
}

export function els(selector) {
  return document.querySelectorAll(selector);
}

export function setHTML(selector, html) {
  const node = typeof selector === 'string' ? document.querySelector(selector) : selector;
  if (node) node.innerHTML = html;
}

export function setText(selector, text) {
  const node = typeof selector === 'string' ? document.querySelector(selector) : selector;
  if (node) node.textContent = text;
}
