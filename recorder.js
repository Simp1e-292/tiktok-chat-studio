// ============================================================================
// recorder.js — Screenshot Engine cho TikTok Chat Studio (Thay thế Video Engine)
// Chụp lại .phone-frame thành file .png chất lượng cao
// ============================================================================

/**
 * Chụp ảnh màn hình điện thoại hiện tại
 */
async function exportScreenshot() {
    const targetElement = document.querySelector('.phone-frame');
    if (!targetElement) {
        alert('⚠️ Không tìm thấy khung video để chụp!');
        return;
    }

    const btn = document.getElementById('btn-screenshot');
    const statusText = document.getElementById('render-status');
    const originalText = btn.innerHTML;

    btn.innerHTML = '⏳ Đang Xử Lý Ảnh...';
    btn.style.opacity = '0.7';
    btn.style.pointerEvents = 'none';
    
    if (statusText) {
        statusText.style.display = 'block';
        statusText.innerHTML = '📸 Đang render ảnh tĩnh chất lượng cao...';
    }

    try {
        if (typeof htmlToImage !== 'undefined') {
            const dataUrl = await htmlToImage.toPng(targetElement, {
                width: targetElement.offsetWidth,
                height: targetElement.offsetHeight,
                pixelRatio: 2.0,
                skipAutoScale: true,
                cacheBust: true,
                useCORS: true,
                skipFonts: true,
                filter: (node) => {
                    if (node && node.style && node.style.display === 'none') return false;
                    return true;
                }
            });

            // Tải file về
            const now = new Date();
            const timestamp = [
                now.getFullYear(),
                String(now.getMonth() + 1).padStart(2, '0'),
                String(now.getDate()).padStart(2, '0'),
                '_',
                String(now.getHours()).padStart(2, '0'),
                String(now.getMinutes()).padStart(2, '0'),
                String(now.getSeconds()).padStart(2, '0')
            ].join('');

            const filename = `TikTok_Chat_Frame_${timestamp}.png`;

            const a = document.createElement('a');
            a.href = dataUrl;
            a.download = filename;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            
            setTimeout(() => {
                document.body.removeChild(a);
            }, 100);

            if (statusText) {
                statusText.innerHTML = `✅ Đã lưu ảnh thành công: ${filename}`;
                setTimeout(() => { statusText.style.display = 'none'; }, 3000);
            }
        } else {
            alert('⚠️ Thư viện chụp ảnh chưa được tải. Hãy kiểm tra kết nối mạng hoặc thử lại.');
        }
    } catch (e) {
        console.error('Lỗi khi chụp ảnh:', e);
        alert('⚠️ Đã xảy ra lỗi khi chụp ảnh. Vui lòng thử lại!');
        if (statusText) statusText.style.display = 'none';
    } finally {
        btn.innerHTML = originalText;
        btn.style.opacity = '1';
        btn.style.pointerEvents = 'auto';
    }
}
