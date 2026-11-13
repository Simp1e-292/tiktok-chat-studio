// ============================================================================
// recorder.js — Screenshot (.PNG) & Live Video Recording (.WEBM) Engine
// Chụp ảnh sắc nét .phone-frame & ghi hình luồng Canvas + Web Audio API
// ============================================================================

let _mediaRecorder = null;
let _recordedChunks = [];
let _isRecording = false;
let _captureActive = false;
let _offscreenCanvas = null;
let _offscreenCtx = null;

function _formatTimestamp() {
    const now = new Date();
    return [
        now.getFullYear(),
        String(now.getMonth() + 1).padStart(2, '0'),
        String(now.getDate()).padStart(2, '0'),
        '_',
        String(now.getHours()).padStart(2, '0'),
        String(now.getMinutes()).padStart(2, '0'),
        String(now.getSeconds()).padStart(2, '0')
    ].join('');
}

function _triggerDownload(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
        if (a.parentNode) document.body.removeChild(a);
    }, 150);
}

/**
 * Chụp ảnh màn hình điện thoại hiện tại (.PNG Retina 2x)
 */
async function exportScreenshot() {
    const targetElement = document.querySelector('.phone-frame');
    if (!targetElement) {
        if (typeof showToast === 'function') showToast('⚠️ Không tìm thấy khung video để chụp!', 'warn');
        else alert('⚠️ Không tìm thấy khung video để chụp!');
        return;
    }

    const btn = document.getElementById('btn-screenshot');
    const statusText = document.getElementById('render-status');
    const originalText = btn ? btn.innerHTML : '';

    if (btn) {
        btn.innerHTML = '⏳ Đang Xử Lý...';
        btn.style.opacity = '0.7';
        btn.style.pointerEvents = 'none';
    }
    if (statusText) {
        statusText.style.display = 'block';
        statusText.innerHTML = '📸 Đang render ảnh tĩnh chất lượng cao...';
    }

    try {
        if (typeof htmlToImage === 'undefined') {
            throw new Error('Thư viện chụp ảnh html-to-image chưa được tải.');
        }

        const dataUrl = await htmlToImage.toPng(targetElement, {
            width: targetElement.offsetWidth,
            height: targetElement.offsetHeight,
            pixelRatio: 2.0,
            skipAutoScale: true,
            cacheBust: false,
            useCORS: true,
            skipFonts: true,
            filter: (node) => !(node && node.style && node.style.display === 'none')
        });

        const filename = `TikTok_Chat_Frame_${_formatTimestamp()}.png`;
        _triggerDownload(dataUrl, filename);

        if (statusText) {
            statusText.innerHTML = `✅ Đã lưu ảnh thành công: ${filename}`;
            setTimeout(() => { statusText.style.display = 'none'; }, 3200);
        }
        if (typeof showToast === 'function') showToast(`✅ Đã tải ảnh: ${filename}`, 'success');
    } catch (e) {
        console.error('Lỗi khi chụp ảnh:', e);
        if (typeof showToast === 'function') showToast('⚠️ Lỗi chụp ảnh: ' + e.message, 'error');
        else alert('⚠️ Đã xảy ra lỗi khi chụp ảnh. Vui lòng thử lại!');
        if (statusText) statusText.style.display = 'none';
    } finally {
        if (btn) {
            btn.innerHTML = originalText;
            btn.style.opacity = '1';
            btn.style.pointerEvents = 'auto';
        }
    }
}

function isRecordingSupported() {
    return typeof MediaRecorder !== 'undefined'
        && typeof HTMLCanvasElement !== 'undefined'
        && typeof HTMLCanvasElement.prototype.captureStream === 'function'
        && typeof htmlToImage !== 'undefined';
}

function isCurrentlyRecording() {
    return _isRecording;
}

function _pickSupportedMimeType() {
    const candidates = [
        'video/webm;codecs=vp9,opus',
        'video/webm;codecs=vp8,opus',
        'video/webm;codecs=vp9',
        'video/webm;codecs=vp8',
        'video/webm'
    ];
    for (const mime of candidates) {
        if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(mime)) {
            return mime;
        }
    }
    return '';
}

async function _captureLoop(targetElement) {
    while (_captureActive && _isRecording) {
        const t0 = performance.now();
        try {
            const snapCanvas = await htmlToImage.toCanvas(targetElement, {
                width: targetElement.offsetWidth,
                height: targetElement.offsetHeight,
                pixelRatio: 1.5,
                skipAutoScale: true,
                cacheBust: false,
                useCORS: true,
                skipFonts: true,
                filter: (node) => !(node && node.style && node.style.display === 'none')
            });
            if (_offscreenCtx && _offscreenCanvas) {
                _offscreenCtx.clearRect(0, 0, _offscreenCanvas.width, _offscreenCanvas.height);
                _offscreenCtx.drawImage(snapCanvas, 0, 0, _offscreenCanvas.width, _offscreenCanvas.height);
            }
        } catch (err) {
            console.warn('[Recorder] Capture frame warning:', err);
        }
        const elapsed = performance.now() - t0;
        const waitMs = Math.max(15, 85 - elapsed);
        await new Promise(r => setTimeout(r, waitMs));
    }
}

async function startVideoRecording() {
    if (_isRecording) return true;

    const targetElement = document.querySelector('.phone-frame');
    if (!targetElement) {
        if (typeof showToast === 'function') showToast('⚠️ Không tìm thấy màn hình video để ghi!', 'warn');
        return false;
    }
    if (!isRecordingSupported()) {
        if (typeof showToast === 'function') showToast('⚠️ Trình duyệt không hỗ trợ MediaRecorder/captureStream.', 'error');
        return false;
    }

    if (typeof initAudio === 'function') initAudio();

    const w = Math.max(360, Math.round(targetElement.offsetWidth * 1.5));
    const h = Math.max(640, Math.round(targetElement.offsetHeight * 1.5));
    _offscreenCanvas = document.createElement('canvas');
    _offscreenCanvas.width = w;
    _offscreenCanvas.height = h;
    _offscreenCtx = _offscreenCanvas.getContext('2d');

    // Chụp ngay frame đầu tiên trước khi mở MediaRecorder
    try {
        const firstSnap = await htmlToImage.toCanvas(targetElement, {
            width: targetElement.offsetWidth,
            height: targetElement.offsetHeight,
            pixelRatio: 1.5,
            skipAutoScale: true,
            cacheBust: false,
            useCORS: true,
            skipFonts: true,
            filter: (node) => !(node && node.style && node.style.display === 'none')
        });
        _offscreenCtx.drawImage(firstSnap, 0, 0, w, h);
    } catch (e) {
        console.warn('[Recorder] First frame warning:', e);
    }

    const canvasStream = _offscreenCanvas.captureStream(30);
    const tracks = [...canvasStream.getVideoTracks()];

    if (typeof window.getStudioAudioStream === 'function') {
        const audStream = window.getStudioAudioStream();
        if (audStream) {
            audStream.getAudioTracks().forEach(t => tracks.push(t));
        }
    }

    const combinedStream = new MediaStream(tracks);
    const mimeType = _pickSupportedMimeType();
    _recordedChunks = [];
    _mediaRecorder = mimeType
        ? new MediaRecorder(combinedStream, { mimeType, videoBitsPerSecond: 3500000 })
        : new MediaRecorder(combinedStream);

    _mediaRecorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size > 0) {
            _recordedChunks.push(ev.data);
        }
    };

    _mediaRecorder.onstop = () => {
        const blob = new Blob(_recordedChunks, { type: mimeType || 'video/webm' });
        const url = URL.createObjectURL(blob);
        const filename = `TikTok_Chat_Video_${_formatTimestamp()}.webm`;
        _triggerDownload(url, filename);
        setTimeout(() => URL.revokeObjectURL(url), 5000);

        const statusText = document.getElementById('render-status');
        if (statusText) {
            statusText.style.display = 'block';
            statusText.innerHTML = `✅ Đã xuất video trình duyệt: ${filename}`;
            setTimeout(() => { statusText.style.display = 'none'; }, 4000);
        }
        if (typeof showToast === 'function') showToast(`🎬 Đã lưu video: ${filename}`, 'success');
    };

    _isRecording = true;
    _captureActive = true;
    _mediaRecorder.start(250);
    _captureLoop(targetElement);

    const btnRecord = document.getElementById('btn-record');
    if (btnRecord) {
        btnRecord.classList.add('recording');
        btnRecord.innerHTML = '⏹ Dừng & Lưu (.WEBM)';
    }
    const statusText = document.getElementById('render-status');
    if (statusText) {
        statusText.style.display = 'block';
        statusText.innerHTML = '🔴 Đang ghi hình... Hãy bấm Phát Demo (hoặc Dừng để xuất file).';
    }
    return true;
}

function stopVideoRecording() {
    if (!_isRecording) return;
    _isRecording = false;
    _captureActive = false;

    const btnRecord = document.getElementById('btn-record');
    if (btnRecord) {
        btnRecord.classList.remove('recording');
        btnRecord.innerHTML = '⏺ Ghi Hình Web (.WEBM)';
    }

    if (_mediaRecorder && _mediaRecorder.state !== 'inactive') {
        _mediaRecorder.stop();
    }
}

async function toggleVideoRecording() {
    if (_isRecording) {
        stopVideoRecording();
    } else {
        await startVideoRecording();
    }
}
