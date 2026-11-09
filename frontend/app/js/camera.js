/**
 * EduFocus — WebRTC Camera Management
 */

let _currentStream = null;

/**
 * Request camera access using getUserMedia.
 * @returns {Promise<MediaStream>}
 */
export async function requestCamera() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    throw new CameraError('unsupported', 'Trình duyệt không hỗ trợ webcam.');
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      audio: false
    });
    _currentStream = stream;
    return stream;
  } catch (err) {
    if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
      throw new CameraError('denied', 'Bạn đã từ chối quyền truy cập camera.');
    }
    if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
      throw new CameraError('unavailable', 'Không tìm thấy camera trên thiết bị.');
    }
    if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
      throw new CameraError('unavailable', 'Camera đang được sử dụng bởi ứng dụng khác.');
    }
    throw new CameraError('unavailable', err.message || 'Không thể truy cập camera.');
  }
}

/**
 * Attach a MediaStream to a <video> element.
 * @param {MediaStream} stream
 * @param {HTMLVideoElement} videoElement
 */
export function attachToVideo(stream, videoElement) {
  if (!videoElement) return;
  videoElement.srcObject = stream;
  videoElement.muted = true;
  videoElement.playsInline = true;
  videoElement.autoplay = true;
  videoElement.play().catch(() => {});
}

/**
 * Stop all tracks in a stream.
 * @param {MediaStream} stream
 */
export function stopCamera(stream) {
  if (!stream) return;
  stream.getTracks().forEach(track => track.stop());
  if (stream === _currentStream) _currentStream = null;
}

/**
 * Stop the currently held stream.
 */
export function stopCurrentCamera() {
  stopCamera(_currentStream);
}

/**
 * Get the current camera status.
 * @returns {'ready'|'idle'}
 */
export function getCameraStatus() {
  if (_currentStream && _currentStream.active) return 'ready';
  return 'idle';
}

// Custom error class for camera errors
export class CameraError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code; // 'denied' | 'unavailable' | 'unsupported' | 'idle'
    this.name = 'CameraError';
  }
}
