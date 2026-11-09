/**
 * EduFocus — Student Prepare Page (WebRTC Camera)
 * Uses real getUserMedia to access the student's webcam.
 */

import { renderShell } from './shell.js';
import { getSession, getCourse } from '../data.js';
import { getCurrentUser } from '../auth.js';
import { esc, badge, btn, toast } from '../ui.js';
import { navigate, getParam } from '../router.js';
import { requestCamera, attachToVideo, stopCurrentCamera, CameraError } from '../camera.js';

let _stream     = null;
let _cameraStatus = 'idle'; // 'idle' | 'requesting' | 'ready' | 'denied' | 'unavailable' | 'unsupported'

export function renderStudentPrepare(params = {}) {
  const sessionId = params.sessionId || getParam('sessionId');
  const courseId  = params.courseId  || getParam('courseId');
  const s = getSession(sessionId);
  const c = s ? getCourse(s.courseId || courseId) : getCourse(courseId);

  _stream       = null;
  _cameraStatus = 'idle';

  const content = `
<div class="breadcrumb">
  <button class="link-btn" data-route="student-home">Trang chủ</button> / Chuẩn bị tham gia
</div>
<div class="page-head">
  <div>
    <div class="eyebrow">CHUẨN BỊ THAM GIA PHIÊN</div>
    <h1 class="h1">${esc(s ? s.title : 'Phiên học')}</h1>
    <p class="sub">${esc(c ? c.name : '')}${s ? ` · ${esc(s.type)} · ${s.duration} phút` : ''}</p>
  </div>
</div>

<div class="grid grid-2" style="gap:24px;align-items:start">
  <!-- Camera test -->
  <div class="card pad">
    <div class="eyebrow" style="margin-bottom:12px">KIỂM TRA CAMERA</div>
    <div class="camera-box" id="camera-preview-box">
      <video id="camera-preview-video" autoplay muted playsinline style="display:none;width:100%;height:100%;border-radius:16px;object-fit:cover"></video>
      <div id="camera-placeholder" class="camera-placeholder">
        <div class="icon">📷</div>
        <h3>Webcam chưa được kết nối</h3>
        <p>Nhấn nút bên dưới để kiểm tra camera của bạn trước khi vào phiên.</p>
        <button class="btn primary" id="btn-start-camera">Bật camera</button>
      </div>
      <div id="camera-denied" class="camera-placeholder hidden">
        <div class="icon">🚫</div>
        <h3>Quyền truy cập camera bị từ chối</h3>
        <p>Bạn cần cấp quyền truy cập camera. Vui lòng kiểm tra cài đặt trình duyệt.</p>
        <button class="btn secondary" id="btn-retry-camera">Thử lại</button>
      </div>
      <div id="camera-unavailable" class="camera-placeholder hidden">
        <div class="icon">⚠️</div>
        <h3>Không tìm thấy camera</h3>
        <p id="camera-err-msg">Thiết bị của bạn không có camera hoặc camera đang bận.</p>
        <button class="btn secondary" id="btn-retry-camera2">Thử lại</button>
      </div>
      <div id="camera-unsupported" class="camera-placeholder hidden">
        <div class="icon">❌</div>
        <h3>Trình duyệt không hỗ trợ</h3>
        <p>Vui lòng sử dụng Chrome, Firefox, Edge hoặc Safari phiên bản mới nhất.</p>
      </div>
      <div id="camera-requesting" class="camera-placeholder hidden">
        <div class="icon" style="animation:spin 1.2s linear infinite;display:inline-block">⏳</div>
        <h3>Đang xin quyền camera…</h3>
        <p>Vui lòng cấp quyền trong hộp thoại của trình duyệt.</p>
      </div>
      <div id="camera-status-chip" class="camera-status hidden"></div>
    </div>
    <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap">
      <button class="btn secondary btn-sm" id="btn-stop-camera" style="display:none">Tắt camera</button>
    </div>
    <div class="notice info" style="margin-top:14px">
      <span>ℹ</span>
      <span>Camera chỉ hoạt động trên kết nối HTTPS hoặc localhost. Dữ liệu video không được gửi đến bất kỳ máy chủ nào trong bản demo này.</span>
    </div>
  </div>

  <!-- Checklist & join -->
  <div>
    <div class="card pad" style="margin-bottom:14px">
      <div class="eyebrow" style="margin-bottom:12px">THÔNG TIN PHIÊN</div>
      ${s ? `
      <div class="status-row"><span>Tên phiên</span><strong>${esc(s.title)}</strong></div>
      <div class="status-row"><span>Loại</span>${badge(s.type, s.type === 'Phiên thi' ? 'b-purple' : 'b-blue')}</div>
      <div class="status-row"><span>Thời lượng</span><strong>${s.duration} phút</strong></div>
      <div class="status-row"><span>Trạng thái</span>${badge(s.status, 'b-green')}</div>
      ` : `<div class="notice warn"><span>⚠</span><span>Không tìm thấy thông tin phiên.</span></div>`}
    </div>

    <div class="card pad" style="margin-bottom:14px">
      <div class="eyebrow" style="margin-bottom:12px">DANH MỤC KIỂM TRA</div>
      <div class="prepare-steps">
        <div class="prepare-step" id="step-camera-check">
          <div class="step-icon">📷</div>
          <div class="step-content">
            <h4>Kiểm tra camera</h4>
            <p id="step-camera-desc">Bật camera và đảm bảo hình ảnh rõ ràng.</p>
          </div>
        </div>
        <div class="prepare-step" id="step-lighting">
          <div class="step-icon">💡</div>
          <div class="step-content">
            <h4>Ánh sáng đầy đủ</h4>
            <p>Đảm bảo khuôn mặt được chiếu sáng tốt, không ngược sáng.</p>
          </div>
        </div>
        <div class="prepare-step" id="step-background">
          <div class="step-icon">🖥️</div>
          <div class="step-content">
            <h4>Môi trường yên tĩnh</h4>
            <p>Chọn không gian không bị phân tâm trong suốt phiên.</p>
          </div>
        </div>
      </div>
    </div>

    <div class="notice warn" style="margin-bottom:14px">
      <span>⚠</span>
      <span>Trong phiên thi, việc rời tab nhiều lần sẽ được ghi nhận. Chỉ sử dụng các tài nguyên được phép.</span>
    </div>

    <button class="btn primary" id="btn-join-session" style="width:100%;font-size:15px;min-height:48px"
      ${_cameraStatus !== 'ready' ? 'disabled' : ''}
      data-session="${esc(sessionId)}" data-course="${esc(courseId)}">
      ✓ Tham gia phiên
    </button>
    <p class="footer-note" id="join-hint" style="text-align:center;margin-top:8px">
      Bật camera trước để có thể tham gia phiên.
    </p>
  </div>
</div>`;

  return renderShell(content, 'student-home');
}

export function initStudentPrepare(params = {}) {
  const sessionId = params.sessionId || getParam('sessionId');
  const courseId  = params.courseId  || getParam('courseId');

  const videoEl       = document.getElementById('camera-preview-video');
  const startBtn      = document.getElementById('btn-start-camera');
  const stopBtn       = document.getElementById('btn-stop-camera');
  const retryBtn      = document.getElementById('btn-retry-camera');
  const retryBtn2     = document.getElementById('btn-retry-camera2');
  const joinBtn       = document.getElementById('btn-join-session');
  const joinHint      = document.getElementById('join-hint');
  const statusChip    = document.getElementById('camera-status-chip');

  async function startCamera() {
    showState('requesting');
    try {
      _stream = await requestCamera();
      attachToVideo(_stream, videoEl);
      _cameraStatus = 'ready';
      showState('ready');
    } catch (err) {
      _cameraStatus = err.code || 'unavailable';
      if (err.code === 'unsupported') showState('unsupported');
      else if (err.code === 'denied')  showState('denied');
      else {
        const msgEl = document.getElementById('camera-err-msg');
        if (msgEl) msgEl.textContent = err.message || 'Không thể truy cập camera.';
        showState('unavailable');
      }
    }
  }

  function showState(state) {
    const states = ['idle', 'requesting', 'ready', 'denied', 'unavailable', 'unsupported'];
    const map = {
      idle:        'camera-placeholder',
      requesting:  'camera-requesting',
      ready:       null,
      denied:      'camera-denied',
      unavailable: 'camera-unavailable',
      unsupported: 'camera-unsupported',
    };

    // Hide all
    document.querySelectorAll('#camera-placeholder, #camera-requesting, #camera-denied, #camera-unavailable, #camera-unsupported').forEach(el => el.classList.add('hidden'));

    if (state === 'ready') {
      videoEl.style.display = 'block';
      statusChip.textContent = '● Camera đang hoạt động';
      statusChip.classList.remove('hidden');
      stopBtn.style.display = 'inline-flex';
      startBtn && (startBtn.style.display = 'none');
      // Update checklist
      const stepCamera = document.getElementById('step-camera-check');
      if (stepCamera) stepCamera.classList.add('done');
      const stepDesc = document.getElementById('step-camera-desc');
      if (stepDesc) stepDesc.textContent = '✓ Camera đã được kết nối và hoạt động tốt.';
      // Enable join
      if (joinBtn) {
        joinBtn.disabled = false;
        joinBtn.style.opacity = '1';
      }
      if (joinHint) joinHint.textContent = 'Camera đã sẵn sàng. Nhấn để tham gia phiên.';
    } else {
      videoEl.style.display = 'none';
      statusChip.classList.add('hidden');
      stopBtn.style.display = 'none';
      if (map[state]) document.getElementById(map[state])?.classList.remove('hidden');
      if (joinBtn)  { joinBtn.disabled = true; joinBtn.style.opacity = ''; }
      if (joinHint) joinHint.textContent = state === 'denied'
        ? 'Cần cấp quyền camera để tham gia phiên.'
        : state === 'unsupported'
        ? 'Trình duyệt không hỗ trợ webcam.'
        : 'Bật camera trước để có thể tham gia phiên.';
    }
  }

  if (startBtn)  startBtn.addEventListener('click', startCamera);
  if (retryBtn)  retryBtn.addEventListener('click', startCamera);
  if (retryBtn2) retryBtn2.addEventListener('click', startCamera);

  if (stopBtn) {
    stopBtn.addEventListener('click', () => {
      if (_stream) { _stream.getTracks().forEach(t => t.stop()); _stream = null; }
      _cameraStatus = 'idle';
      showState('idle');
      startBtn && (startBtn.style.display = '');
    });
  }

  if (joinBtn) {
    joinBtn.addEventListener('click', () => {
      if (_cameraStatus !== 'ready') {
        toast('Vui lòng bật camera trước khi tham gia phiên.');
        return;
      }
      // Store stream reference for student-live page
      window.__edufocus_camera_stream = _stream;
      navigate('student-live', { sessionId, courseId });
    });
  }

  // Stop camera when navigating away
  window.__edufocus_prepare_cleanup = () => {
    if (_stream && _cameraStatus !== 'ready') {
      _stream.getTracks().forEach(t => t.stop());
      _stream = null;
    }
  };
}

// Spin animation is defined in index.html / pages.css

