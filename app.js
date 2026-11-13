// ============================================================================
// app.js — Core Controller cho TikTok Chat Studio Pro (v4.0)
// Quản lý: Nhân vật (Avatar + Giọng AI/Thu âm), Kịch bản (IndexedDB + JSON + AI),
// Trình phát Demo đồng bộ Web Audio/Edge-TTS, FB Post, Group Chat & Export CapCut/MP4
// ============================================================================

// 1. QUẢN LÝ NHÂN VẬT, AVATAR & GIỌNG ĐỌC
// ============================================================================
const defaultCharacters = [
    {
        id: "char_sep",
        name: "SẾP TỔNG",
        avatar: "assets/avatar_sep.png",
        role: "owner",
        pitch: 0.95,
        voice: "vi-VN-NamMinhNeural"
    },
    {
        id: "char_hai",
        name: "Hải Kỹ Thuật",
        avatar: "assets/avatar_hai.png",
        role: "customer",
        pitch: 1.05,
        voice: "vi-VN-NamMinhNeural"
    },
    {
        id: "char_vy",
        name: "Vy Dự Án (Sale)",
        avatar: "assets/avatar_vy.png",
        role: "customer",
        pitch: 1.25,
        voice: "vi-VN-HoaiMyNeural"
    },
    {
        id: "char_thang",
        name: "Thắng Công Trình",
        avatar: "assets/avatar_thang.png",
        role: "customer",
        pitch: 1.1,
        voice: "vi-VN-NamMinhNeural"
    },
    {
        id: "char_cuathep_vip",
        name: "Cửa Thép Luxury",
        avatar: "assets/steel_door_logo.png",
        role: "owner",
        pitch: 0.95,
        voice: "vi-VN-NamMinhNeural"
    },
    {
        id: "char_owner_coba",
        name: "Tạp Hóa & Sức Khỏe Cô Ba",
        avatar: "assets/owner_avatar.png",
        role: "owner",
        pitch: 0.95,
        voice: "vi-VN-HoaiMyNeural"
    },
    {
        id: "char_cust_sieuhai",
        name: "Anh Sinh Viên Siêu Hài",
        avatar: "assets/customer_avatar.png",
        role: "customer",
        pitch: 1.2,
        voice: "vi-VN-NamMinhNeural"
    },
    {
        id: "char_cust_sinhvien",
        name: "Anh Khách Nhậu 3 Đêm",
        avatar: "assets/customer_avatar.png",
        role: "customer",
        pitch: 1.1,
        voice: "vi-VN-NamMinhNeural"
    }
];

let characterRoster = defaultCharacters.map(c => ({ ...c }));
let uploadedAvatarBase64 = "assets/customer_avatar.png";
let uploadedVoiceDataUrl = null;
let editingCharIndex = null;
let _dbReady = false;

let serverAvailable = false;
let serverCapabilities = {};

function escapeHtml(str) {
    return String(str ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function showToast(message, type = 'info', duration = 3600) {
    const el = document.getElementById('studio-toast');
    if (!el) return;
    el.className = `studio-toast ${type} show`;
    el.textContent = message;
    if (showToast._timer) clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => {
        el.classList.remove('show');
    }, duration);
}

function inferDefaultVoice(char) {
    if (char && char.voice) return char.voice;
    const nameL = String(char?.name || '').toLowerCase();
    const pitch = Number(char?.pitch || 1.0);
    const femaleHints = ['vy', 'cô ', 'chị ', 'nữ', 'lan', 'mai', 'hoa', 'linh', 'ngọc', 'trang'];
    if (femaleHints.some(h => nameL.includes(h)) || pitch >= 1.22) {
        return 'vi-VN-HoaiMyNeural';
    }
    return 'vi-VN-NamMinhNeural';
}

function normalizeCharacterItem(c) {
    return {
        ...c,
        pitch: Number(c?.pitch) || 1.0,
        voice: inferDefaultVoice(c),
        avatar: c?.avatar || 'assets/customer_avatar.png'
    };
}

function buildExportSlug(rawTitle, fallback = 'TikTok_Chat_Project') {
    const noTone = String(rawTitle || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/đ/g, 'd')
        .replace(/Đ/g, 'D');
    const clean = noTone.replace(/[^A-Za-z0-9_-]+/g, '_').replace(/^_+|_+$/g, '');
    return (clean.slice(0, 44) || fallback);
}

// Lưu nhân vật vào IndexedDB (primary) và localStorage gọn nhẹ (fallback)
function saveCharactersToStorage() {
    if (_dbReady && typeof saveCharactersToIndexedDB === 'function') {
        saveCharactersToIndexedDB(characterRoster).catch(e => {
            console.error('IndexedDB save characters error:', e);
        });
    }
    try {
        // Bỏ file âm thanh thu âm lớn khỏi localStorage fallback để không bị QuotaExceededError
        const slimRoster = characterRoster.map(c => {
            const copy = { ...c };
            delete copy.customVoiceDataUrl;
            return copy;
        });
        localStorage.setItem('tiktok_studio_characters_v2', JSON.stringify(slimRoster));
    } catch (e) {
        console.warn('localStorage save skipped (IndexedDB is primary):', e.message);
    }
}

function updateVoiceUploadStatusUI() {
    const statusEl = document.getElementById('char-voice-status');
    const clearBtn = document.getElementById('btn-clear-char-voice');
    if (!statusEl) return;
    if (uploadedVoiceDataUrl) {
        statusEl.textContent = '🎵 Đã gắn file giọng thu âm riêng';
        statusEl.style.color = '#34d399';
        if (clearBtn) clearBtn.style.display = 'inline-flex';
    } else {
        const voiceVal = document.getElementById('char-input-voice')?.value || 'vi-VN-NamMinhNeural';
        statusEl.textContent = voiceVal.includes('HoaiMy')
            ? '🤖 Dùng AI: Hoài My (Nữ Tự Nhiên)'
            : '🤖 Dùng AI: Nam Minh (Nam Trầm)';
        statusEl.style.color = '#94a3b8';
        if (clearBtn) clearBtn.style.display = 'none';
    }
}

function clearCharacterCustomVoice() {
    uploadedVoiceDataUrl = null;
    const fileIn = document.getElementById('char-input-voice-file');
    if (fileIn) fileIn.value = '';
    updateVoiceUploadStatusUI();
    showToast('🗑️ Đã xóa file giọng thu âm riêng trên form.', 'info', 2400);
}

function handleVoiceFileSelect(input) {
    const file = input?.files?.[0];
    if (!file) return;
    if (file.size > 8 * 1024 * 1024) {
        showToast('⚠️ File âm thanh vượt quá 8MB! Hãy chọn file ngắn dưới 8MB.', 'warn');
        input.value = '';
        return;
    }
    const reader = new FileReader();
    reader.onload = function (e) {
        uploadedVoiceDataUrl = e.target.result;
        updateVoiceUploadStatusUI();
        showToast('✅ Đã nạp file giọng riêng thành công!', 'success', 2400);
    };
    reader.readAsDataURL(file);
}

function previewCharacterVoice() {
    initAudio();
    const nameVal = document.getElementById('char-input-name')?.value?.trim() || 'Nhân vật';
    const voiceVal = document.getElementById('char-input-voice')?.value || 'vi-VN-NamMinhNeural';
    const pitchVal = parseFloat(document.getElementById('char-input-pitch')?.value || '1.0');
    const sampleText = `Xin chào! Tôi là ${nameVal}, rất vui được đồng hành cùng bạn trên TikTok Chat Studio.`;
    speakText(sampleText, {
        name: nameVal,
        voice: voiceVal,
        pitch: pitchVal,
        customVoiceDataUrl: uploadedVoiceDataUrl
    });
}

// Hiển thị danh sách nhân vật
function renderCharacterRoster() {
    const container = document.getElementById('character-list-container');
    if (!container) return;
    container.innerHTML = '';

    characterRoster.forEach((char, idx) => {
        const isOwner = char.role === 'owner';
        const isBeingEdited = (editingCharIndex === idx);
        const voiceLabel = char.customVoiceDataUrl
            ? '🎵 Thu âm riêng'
            : (inferDefaultVoice(char).includes('HoaiMy') ? '👩 Hoài My' : '👨 Nam Minh');

        const card = document.createElement('div');
        card.className = `character-card ${isBeingEdited ? 'editing' : ''}`;
        card.innerHTML = `
            <div class="character-info">
                <div class="char-avatar-box">
                    <img src="${escapeHtml(char.avatar || 'assets/customer_avatar.png')}" alt="Avatar" onerror="this.src='assets/customer_avatar.png'">
                </div>
                <div class="char-details">
                    <h4>${escapeHtml(char.name)}</h4>
                    <span class="char-badge ${isOwner ? 'owner' : 'customer'}">
                        ${isOwner ? '👑 Chủ Tiệm / Shop' : '💬 Khách Hàng'} • ${escapeHtml(voiceLabel)}
                    </span>
                </div>
            </div>
            <div class="char-actions">
                <button type="button" class="btn-icon-action edit" onclick="editCharacter(${idx})" title="Chỉnh sửa nhân vật này">✏️</button>
                <button type="button" class="btn-icon-action delete" onclick="deleteCharacter(${idx})" title="Xóa nhân vật này">🗑️</button>
            </div>
        `;
        container.appendChild(card);
    });

    updateBuilderParticipantDropdowns();
}

function editCharacter(idx) {
    const char = characterRoster[idx];
    if (!char) return;

    editingCharIndex = idx;

    const formCard = document.getElementById('char-form-card');
    const formTitle = document.getElementById('char-form-title');
    const nameInput = document.getElementById('char-input-name');
    const roleInput = document.getElementById('char-input-role');
    const pitchInput = document.getElementById('char-input-pitch');
    const voiceInput = document.getElementById('char-input-voice');
    const btnSubmit = document.getElementById('btn-save-char');
    const btnCancel = document.getElementById('btn-cancel-edit-char');
    const previewEl = document.getElementById('avatar-preview-img');

    if (formCard) formCard.classList.add('edit-mode');
    if (formTitle) formTitle.innerHTML = `✏️ Đang Chỉnh Sửa: <strong>${escapeHtml(char.name)}</strong>`;
    if (nameInput) nameInput.value = char.name;
    if (roleInput) roleInput.value = char.role || 'customer';
    if (pitchInput) pitchInput.value = char.pitch ? String(char.pitch) : '1.1';
    if (voiceInput) voiceInput.value = inferDefaultVoice(char);

    uploadedAvatarBase64 = char.avatar || 'assets/customer_avatar.png';
    uploadedVoiceDataUrl = char.customVoiceDataUrl || null;
    if (previewEl) previewEl.src = uploadedAvatarBase64;
    updateVoiceUploadStatusUI();

    if (btnSubmit) btnSubmit.innerHTML = '💾 Cập Nhật Nhân Vật Này';
    if (btnCancel) btnCancel.style.display = 'inline-flex';

    renderCharacterRoster();

    if (formCard) {
        formCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function cancelEditCharacter() {
    editingCharIndex = null;

    const formCard = document.getElementById('char-form-card');
    const formTitle = document.getElementById('char-form-title');
    const nameInput = document.getElementById('char-input-name');
    const voiceInput = document.getElementById('char-input-voice');
    const btnSubmit = document.getElementById('btn-save-char');
    const btnCancel = document.getElementById('btn-cancel-edit-char');
    const previewEl = document.getElementById('avatar-preview-img');
    const fileInput = document.getElementById('char-input-avatar-file');
    const voiceFileInput = document.getElementById('char-input-voice-file');

    if (formCard) formCard.classList.remove('edit-mode');
    if (formTitle) formTitle.innerHTML = '➕ Thêm Nhân Vật Mới Vào Studio';
    if (nameInput) nameInput.value = '';
    if (voiceInput) voiceInput.value = 'vi-VN-NamMinhNeural';
    if (fileInput) fileInput.value = '';
    if (voiceFileInput) voiceFileInput.value = '';

    uploadedAvatarBase64 = 'assets/customer_avatar.png';
    uploadedVoiceDataUrl = null;
    if (previewEl) previewEl.src = 'assets/customer_avatar.png';
    updateVoiceUploadStatusUI();

    if (btnSubmit) btnSubmit.innerHTML = '💾 Lưu & Thêm Vào Dàn Nhân Vật';
    if (btnCancel) btnCancel.style.display = 'none';

    renderCharacterRoster();
}

// Tự động nén & thu nhỏ avatar qua Canvas (tối đa 220px)
function handleAvatarFileSelect(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const reader = new FileReader();
        reader.onload = function (e) {
            const img = new Image();
            img.onload = function () {
                const maxDim = 220;
                let w = img.width;
                let h = img.height;
                if (w > maxDim || h > maxDim) {
                    if (w > h) {
                        h = Math.round((h * maxDim) / w);
                        w = maxDim;
                    } else {
                        w = Math.round((w * maxDim) / h);
                        h = maxDim;
                    }
                }
                const canvas = document.createElement('canvas');
                canvas.width = w;
                canvas.height = h;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, w, h);

                uploadedAvatarBase64 = canvas.toDataURL('image/jpeg', 0.85);
                const previewEl = document.getElementById('avatar-preview-img');
                if (previewEl) previewEl.src = uploadedAvatarBase64;
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
}

function saveOrUpdateCharacter() {
    const nameInput = document.getElementById('char-input-name');
    const roleInput = document.getElementById('char-input-role');
    const pitchInput = document.getElementById('char-input-pitch');
    const voiceInput = document.getElementById('char-input-voice');

    if (!nameInput || !nameInput.value.trim()) {
        showToast('⚠️ Vui lòng nhập tên cho nhân vật / shop của bạn!', 'warn');
        if (nameInput) nameInput.focus();
        return;
    }

    const nameVal = nameInput.value.trim();
    const roleVal = roleInput ? roleInput.value : 'customer';
    const pitchVal = pitchInput ? (parseFloat(pitchInput.value) || 1.0) : 1.0;
    const voiceVal = voiceInput ? voiceInput.value : 'vi-VN-NamMinhNeural';

    if (editingCharIndex !== null && characterRoster[editingCharIndex]) {
        const updatedChar = characterRoster[editingCharIndex];
        updatedChar.name = nameVal;
        updatedChar.role = roleVal;
        updatedChar.pitch = pitchVal;
        updatedChar.voice = voiceVal;
        updatedChar.avatar = uploadedAvatarBase64;
        if (uploadedVoiceDataUrl) {
            updatedChar.customVoiceDataUrl = uploadedVoiceDataUrl;
        } else {
            delete updatedChar.customVoiceDataUrl;
        }

        // Đồng bộ tên mới trong kịch bản group nếu tin nhắn đang trỏ tới nhân vật này
        Object.values(scenarios).forEach(sc => {
            if (sc && Array.isArray(sc.messages)) {
                sc.messages.forEach(m => {
                    if (m.senderId === updatedChar.id) {
                        m.senderName = updatedChar.name;
                    }
                });
            }
        });

        saveCharactersToStorage();
        saveScenariosToStorage();
        cancelEditCharacter();
        refreshCurrentStageDisplay();
        renderScriptBuilder();
        showToast(`✅ Đã cập nhật nhân vật "${updatedChar.name}"!`, 'success');
    } else {
        const newChar = {
            id: 'char_' + Date.now(),
            name: nameVal,
            avatar: uploadedAvatarBase64,
            role: roleVal,
            pitch: pitchVal,
            voice: voiceVal
        };
        if (uploadedVoiceDataUrl) {
            newChar.customVoiceDataUrl = uploadedVoiceDataUrl;
        }

        characterRoster.push(newChar);
        saveCharactersToStorage();
        cancelEditCharacter();
        refreshCurrentStageDisplay();
        renderScriptBuilder();
        showToast(`🎉 Đã thêm mới nhân vật "${newChar.name}"!`, 'success');
    }
}

function deleteCharacter(idx) {
    if (characterRoster.length <= 1) {
        showToast('⚠️ Cần giữ lại ít nhất 01 nhân vật trong Studio!', 'warn');
        return;
    }

    const target = characterRoster[idx];
    if (!target) return;
    if (confirm(`Bạn có chắc muốn xóa nhân vật "${target.name}" khỏi hệ thống không?`)) {
        if (editingCharIndex === idx) {
            cancelEditCharacter();
        } else if (editingCharIndex !== null && editingCharIndex > idx) {
            editingCharIndex--;
        }

        characterRoster.splice(idx, 1);
        saveCharactersToStorage();
        renderCharacterRoster();
        refreshCurrentStageDisplay();
        showToast(`🗑️ Đã xóa nhân vật "${target.name}".`, 'info');
    }
}


// ============================================================================
// 2. DỮ LIỆU KỊCH BẢN MẶC ĐỊNH & PERSISTENCE (INDEXEDDB + JSON + GEMINI AI)
// ============================================================================
const DEFAULT_SCENARIOS = {
    scenario_group_cuathep: {
        title: "🏢 [HÀI HƯỚC CHỐT CỌC] Bác Đại Gia Test Cách Âm & Chó Bec-Giê Bọc Răng Sứ",
        desc: "Drama hài hước đi chốt cọc 100 bộ cửa thép: Bác đại gia test cách âm chống vợ cằn nhằn, chó cắn gãy răng, cọc 200 triệu trừ 2 triệu làm răng chó.",
        theme: "group_messenger",
        groupName: "Văn Phòng Cửa Thép Luxury",
        groupUnread: 8,
        groupAvatar: "assets/steel_door_logo.png",
        bgWallpaper: "assets/bg_anime_sky.jpg",
        bubbleColor: "#e0f2fe",
        messages: [
            {
                id: "gmsg_1",
                senderId: "char_sep",
                senderName: "SẾP TỔNG",
                sender: "owner",
                type: "text",
                content: "Vy ơi! Tình hình đi chốt cọc 100 bộ cửa thép biệt thự cho bác đại gia thế nào rồi?!",
                delay: 1600,
                sfx: "pop"
            },
            {
                id: "gmsg_2",
                senderId: "char_vy",
                senderName: "Vy Dự Án (Sale)",
                sender: "customer",
                type: "text",
                content: "Ban đầu bác chủ nhà khó tính lắm Sếp, bảo cửa thép mà không cách âm thì không lấy! 😅",
                delay: 1500,
                sfx: "ting"
            },
            {
                id: "gmsg_3",
                senderId: "char_hai",
                senderName: "Hải Kỹ Thuật",
                sender: "customer",
                type: "text",
                content: "Thế là em đứng ngoài gào như loa phường, còn bác đứng trong phòng nghe nhạc thiền êm ru Sếp ạ! 😂",
                delay: 1500,
                sfx: "ting"
            },
            {
                id: "gmsg_4",
                senderId: "char_thang",
                senderName: "Thắng Công Trình",
                sender: "customer",
                type: "text",
                content: "Chưa hết đâu Sếp, bác còn dắt cả con chó Bec-giê ra cắn thử cửa, chó gãy cụt mất một cái răng! 🐕",
                delay: 1500,
                sfx: "ting"
            },
            {
                id: "gmsg_5",
                senderId: "char_vy",
                senderName: "Vy Dự Án (Sale)",
                sender: "customer",
                type: "text",
                content: "Bác ưng quá cười bảo: 'Cửa này vợ tao cằn nhằn đóng cửa là yên tĩnh tuyệt đối!' Bác chuyển cọc luôn 200 triệu! 💸",
                delay: 1600,
                sfx: "ting"
            },
            {
                id: "gmsg_6",
                senderId: "char_sep",
                senderName: "SẾP TỔNG",
                sender: "owner",
                type: "text",
                content: "Haha đỉnh quá! Thế tiền cọc 200 triệu đã nổi trong tài khoản công ty chưa?!",
                delay: 1500,
                sfx: "pop"
            },
            {
                id: "gmsg_7",
                senderId: "char_vy",
                senderName: "Vy Dự Án (Sale)",
                sender: "customer",
                type: "text",
                content: "Dạ nổi rồi ạ! Nhưng bác trừ lại 2 triệu tiền đi bọc răng sứ cho con Bec-giê Sếp ơi! 🦷",
                delay: 1500,
                sfx: "ting"
            },
            {
                id: "gmsg_8",
                senderId: "char_sep",
                senderName: "SẾP TỔNG",
                sender: "owner",
                type: "text",
                content: "Trừ vào lương Hải! Còn lại tối nay Sếp bao cả công ty liên hoan bia hơi ăn mừng! Duyệt luôn! 👍",
                delay: 1200,
                sfx: "pop"
            }
        ]
    },
    scenario_1: {
        title: "🔥 Tư vấn Vitamin C cho Khách Thức Đêm",
        desc: "Anh sinh viên chạy deadline xin thuốc siêu nhân & sự tư vấn cực mượt kèm giỏ hàng Vitamin C Kháng Mỏi + Sticker Like.",
        theme: "messenger_ios",
        ownerCharId: "char_owner_coba",
        customerCharId: "char_cust_sieuhai",
        messages: [
            {
                id: "msg_1",
                sender: "customer",
                type: "text",
                content: "Shop ơi, dạo này em thức đêm chạy công việc đuối quá, bên mình có dòng vitamin nào cho ngày mới sung sức không ạ? 😭",
                delay: 1400,
                sfx: "ting"
            },
            {
                id: "msg_2",
                sender: "owner",
                type: "text",
                content: "Dạ có ngay! Bên shop có dòng Bảo Bối cứu rỗi tinh thần cho bạn đây, đợi bên mình lấy thông tin cho bạn nhé... ⚡",
                delay: 1600,
                sfx: "pop"
            },
            {
                id: "msg_3",
                sender: "owner",
                type: "product_card",
                content: "Vitamin C Kháng Mỏi - Giải nạp năng lượng tức thì cho ngày dài sung sức",
                image: "assets/vitamin_c.png",
                price: "120.000₫",
                discount: "-20% HÔM NAY",
                cta: "🛍 Chốt ngay trên TikTok Shop",
                delay: 1800,
                sfx: "special"
            },
            {
                id: "msg_4",
                sender: "customer",
                type: "text",
                content: "Chất quá shop ơi! Cho em 2 hộp luôn nhé, đang rất cần để chiến nốt công việc! 🔥",
                delay: 1500,
                sfx: "ting"
            },
            {
                id: "msg_5",
                sender: "owner",
                type: "text",
                content: "Dạ chốt đơn ạ! Nhớ pha với nước mát uống buổi sáng và trưa để đạt hiệu quả tốt nhất nhé! 💚",
                delay: 1500,
                sfx: "pop"
            },
            {
                id: "msg_6",
                sender: "owner",
                type: "like_sticker",
                content: "👍",
                delay: 800,
                sfx: "pop"
            }
        ]
    },
    scenario_2: {
        title: "🍻 Giải Nhanh Nóng Gan Cho Anh Nhậu 3 Ngày",
        desc: "Khách quen than thở sau những bữa tiệc rực lửa và pha chốt đơn Trà Thảo Mộc mát rượi kèm thả Like.",
        theme: "messenger_ios",
        ownerCharId: "char_owner_coba",
        customerCharId: "char_cust_sinhvien",
        messages: [
            {
                id: "msg_1",
                sender: "customer",
                type: "text",
                content: "Shop ơi cứu! Nhậu 3 đêm liền giờ người nóng như lửa đốt, có món gì thảo mộc hạ nhiệt không shop?",
                delay: 1400,
                sfx: "ting"
            },
            {
                id: "msg_2",
                sender: "owner",
                type: "text",
                content: "Trời đất ơi! Chào mừng bạn tới chuyên gia thanh lọc gan! Chờ 30 giây rước Trà Bảo Bối về nè...",
                delay: 1600,
                sfx: "pop"
            },
            {
                id: "msg_3",
                sender: "owner",
                type: "product_card",
                content: "Trà Thảo Mộc Giải Độc Gan Siêu Tốc - Mát Rượi Tức Thì",
                image: "assets/vitamin_c.png",
                price: "95.000₫",
                discount: "SIÊU SALE 15%",
                cta: "🛍 Mua hàng ngay giảm 15%",
                delay: 1900,
                sfx: "special"
            },
            {
                id: "msg_4",
                sender: "customer",
                type: "text",
                content: "Đúng chân ái! Chốt cho em 3 hộp nha, chiều mát em qua xách về liền!",
                delay: 1400,
                sfx: "ting"
            },
            {
                id: "msg_5",
                sender: "customer",
                type: "like_sticker",
                content: "👍",
                delay: 800,
                sfx: "ting"
            }
        ]
    }
};

function attachLegacyScenarioAliases(obj) {
    if (!Object.getOwnPropertyDescriptor(obj, 'scenario_group_petbite')) {
        Object.defineProperty(obj, 'scenario_group_petbite', {
            enumerable: false,
            configurable: true,
            get() {
                return this.scenario_group_cuathep;
            }
        });
    }
    return obj;
}

let scenarios = attachLegacyScenarioAliases(JSON.parse(JSON.stringify(DEFAULT_SCENARIOS)));
let currentScenarioKey = 'scenario_1';

function saveScenariosToStorage() {
    if (!_dbReady || typeof saveAllScenariosToIndexedDB !== 'function') return;
    const plain = {};
    Object.keys(scenarios).forEach(k => {
        if (scenarios[k] && typeof scenarios[k] === 'object') {
            plain[k] = scenarios[k];
        }
    });
    saveAllScenariosToIndexedDB(plain).catch(e => {
        console.error('IndexedDB save scenarios error:', e);
    });
}

function renderScenarioCards() {
    const container = document.getElementById('scenario-list-container');
    if (!container) return;
    container.innerHTML = '';

    const keys = Object.keys(scenarios);
    if (keys.length === 0) return;

    keys.forEach(key => {
        const sc = scenarios[key];
        if (!sc) return;
        const isGroup = sc.theme === 'group_messenger';
        const isActive = key === currentScenarioKey;
        const msgCount = Array.isArray(sc.messages) ? sc.messages.length : 0;
        const hasProduct = Array.isArray(sc.messages) && sc.messages.some(m => m.type === 'product_card' || m.type === 'product');
        const hasSticker = Array.isArray(sc.messages) && sc.messages.some(m => m.type === 'like_sticker' || m.type === 'sticker');

        const card = document.createElement('div');
        card.className = `scenario-card ${isActive ? 'active' : ''}`;
        card.id = `card-${key}`;
        if (isGroup) card.style.borderLeft = '3px solid #38bdf8';
        card.onclick = () => openScenarioFromCard(key);

        card.innerHTML = `
            <div class="scenario-card-header">
                <h4>${escapeHtml(sc.title || key)}</h4>
                <button type="button" class="scenario-delete-btn" onclick="event.stopPropagation(); deleteScenario('${escapeHtml(key)}')" title="Xóa kịch bản này">🗑️</button>
            </div>
            <p>${escapeHtml(sc.desc || (isGroup ? 'Kịch bản Group Chat nhiều nhân vật.' : 'Kịch bản Chat 1-1 chốt đơn TikTok.'))}</p>
            <div class="scenario-meta">
                ${isGroup
                    ? '<span class="meta-tag" style="background: rgba(56,189,248,0.15); color: #38bdf8;">🏢 Group Chat</span>'
                    : '<span class="meta-tag" style="background: rgba(16,185,129,0.15); color: #34d399;">💬 Chat 1-1</span>'}
                <span class="meta-tag">⚡ ${msgCount} Tin nhắn</span>
                ${hasProduct ? '<span class="meta-tag">📦 Product Card</span>' : ''}
                ${hasSticker ? '<span class="meta-tag">👍 Sticker Like</span>' : ''}
            </div>
        `;
        container.appendChild(card);
    });
}

function openScenarioFromCard(key) {
    const sc = scenarios[key];
    if (!sc) return;
    const targetMode = sc.theme === 'group_messenger' ? 'group' : 'chat';
    currentStudioMode = targetMode;
    syncModeButtonsAndPanels(targetMode);
    selectScenario(key);
    switchTab('builder');
}

function deleteScenario(key) {
    const keys = Object.keys(scenarios);
    if (keys.length <= 1) {
        showToast('⚠️ Cần giữ lại ít nhất 01 kịch bản trong Studio!', 'warn');
        return;
    }
    const target = scenarios[key];
    if (!target) return;
    if (!confirm(`Bạn có chắc muốn xóa kịch bản "${target.title}"?`)) return;

    delete scenarios[key];
    if (_dbReady && typeof deleteScenarioFromIndexedDB === 'function') {
        deleteScenarioFromIndexedDB(key).catch(e => console.error(e));
    }
    saveScenariosToStorage();

    if (currentScenarioKey === key) {
        const nextKey = Object.keys(scenarios)[0];
        const nextSc = scenarios[nextKey];
        currentScenarioKey = nextKey;
        const targetMode = nextSc.theme === 'group_messenger' ? 'group' : 'chat';
        currentStudioMode = targetMode;
        syncModeButtonsAndPanels(targetMode);
        selectScenario(nextKey);
    } else {
        renderScenarioCards();
    }
    showToast('🗑️ Đã xóa kịch bản.', 'info');
}

function resetDefaultScenarios() {
    if (!confirm('Khôi phục toàn bộ kịch bản mẫu gốc (Cửa Thép Luxury + Cô Ba Vitamin C + Trà Thảo Mộc)? Các kịch bản bạn tự tạo vẫn sẽ bị thay thế bởi bộ gốc.')) {
        return;
    }
    scenarios = attachLegacyScenarioAliases(JSON.parse(JSON.stringify(DEFAULT_SCENARIOS)));
    if (_dbReady && typeof saveAllScenariosToIndexedDB === 'function') {
        saveAllScenariosToIndexedDB(scenarios).catch(e => console.error(e));
    }
    currentScenarioKey = currentStudioMode === 'group' ? 'scenario_group_cuathep' : 'scenario_1';
    selectScenario(currentScenarioKey);
    renderScenarioCards();
    showToast('🔄 Đã khôi phục bộ kịch bản mẫu gốc!', 'success');
}

function exportScenarioJsonFile() {
    const sc = scenarios[currentScenarioKey];
    if (!sc) return;
    const payload = {
        scenarioKey: currentScenarioKey,
        scenario: sc,
        characters: characterRoster.map(c => {
            const copy = { ...c };
            return copy;
        }),
        exportedAt: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${buildExportSlug(sc.title, currentScenarioKey)}.json`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
        if (a.parentNode) document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 200);
    showToast('📤 Đã xuất file JSON (tương thích 100% CapCut & MP4 CLI)!', 'success');
}

function importScenarioJsonFile(input) {
    const file = input?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function (e) {
        try {
            const parsed = JSON.parse(e.target.result);
            let importedScenario = null;
            let importedChars = null;

            if (parsed && parsed.scenario && Array.isArray(parsed.scenario.messages)) {
                importedScenario = parsed.scenario;
                importedChars = parsed.characters;
            } else if (parsed && Array.isArray(parsed.messages)) {
                importedScenario = parsed;
            } else {
                throw new Error('File JSON không đúng định dạng kịch bản (thiếu trường messages).');
            }

            if (Array.isArray(importedChars)) {
                let charsChanged = false;
                importedChars.forEach(ic => {
                    if (ic && ic.id && !characterRoster.some(c => c.id === ic.id)) {
                        characterRoster.push(normalizeCharacterItem(ic));
                        charsChanged = true;
                    }
                });
                if (charsChanged) {
                    saveCharactersToStorage();
                    renderCharacterRoster();
                }
            }

            const newKey = 'scenario_import_' + Date.now();
            scenarios[newKey] = importedScenario;
            saveScenariosToStorage();
            openScenarioFromCard(newKey);
            renderScenarioCards();
            showToast(`📥 Đã nhập kịch bản: "${importedScenario.title || newKey}"`, 'success');
        } catch (err) {
            showToast('⚠️ Lỗi đọc file JSON: ' + err.message, 'error');
        } finally {
            input.value = '';
        }
    };
    reader.readAsText(file, 'utf-8');
}

function toggleAiBox() {
    const box = document.getElementById('ai-generator-box');
    if (!box) return;
    const isHidden = box.style.display === 'none' || !box.style.display;
    box.style.display = isHidden ? 'flex' : 'none';
}

async function generateWithAI() {
    const topic = document.getElementById('ai-topic-input')?.value?.trim();
    const aiMode = document.getElementById('ai-mode-select')?.value || 'group';
    const apiKey = document.getElementById('ai-api-key')?.value?.trim();
    const saveKey = document.getElementById('ai-save-key')?.checked;
    const btn = document.getElementById('btn-run-ai');

    if (!topic) {
        showToast('⚠️ Hãy nhập chủ đề hoặc sản phẩm cần viết kịch bản!', 'warn');
        return;
    }
    if (!apiKey) {
        showToast('⚠️ Hãy nhập Gemini API Key để AI tạo kịch bản!', 'warn');
        return;
    }

    if (_dbReady && typeof saveSetting === 'function') {
        saveSetting('gemini_api_key', saveKey ? apiKey : '').catch(() => {});
    }

    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '⏳ Đang sáng tạo kịch bản viral...';
    }

    try {
        const charSummary = characterRoster
            .map(c => `- id="${c.id}", name="${c.name}", role="${c.role}"`)
            .join('\n');

        const prompt = aiMode === 'group'
            ? `Viết 1 kịch bản Group Chat Messenger hài hước, cuốn hút dài 7-8 câu để làm video TikTok bán/quảng bá chủ đề: "${topic}".
Danh sách nhân vật hiện có (BẮT BUỘC dùng đúng senderId và senderName trong danh sách này):
${charSummary}

Trả về DUY NHẤT 1 JSON object hợp lệ (không giải thích thêm) theo schema:
{
  "title": "Tiêu đề ngắn gọn hấp dẫn",
  "desc": "Mô tả 1 câu ngắn",
  "theme": "group_messenger",
  "groupName": "Tên nhóm chat phù hợp",
  "groupUnread": 8,
  "groupAvatar": "assets/steel_door_logo.png",
  "bgWallpaper": "assets/bg_anime_sky.jpg",
  "bubbleColor": "#e0f2fe",
  "messages": [
    { "id": "g1", "senderId": "...", "senderName": "...", "sender": "owner hoặc customer", "type": "text", "content": "...", "delay": 1500, "sfx": "pop hoặc ting" }
  ]
}`
            : `Viết 1 kịch bản Chat Messenger 1-1 bán hàng viral dài 6 câu (có 1 product_card và 1 like_sticker) về chủ đề: "${topic}".
Chọn 1 owner (id bắt đầu bằng char_) và 1 customer từ danh sách sau:
${charSummary}

Trả về DUY NHẤT 1 JSON object hợp lệ (không giải thích thêm) theo schema:
{
  "title": "Tiêu đề ngắn gọn",
  "desc": "Mô tả 1 câu",
  "theme": "messenger_ios",
  "ownerCharId": "...",
  "customerCharId": "...",
  "messages": [
    { "id": "m1", "sender": "customer", "type": "text", "content": "...", "delay": 1400, "sfx": "ting" },
    { "id": "m2", "sender": "owner", "type": "text", "content": "...", "delay": 1500, "sfx": "pop" },
    { "id": "m3", "sender": "owner", "type": "product_card", "content": "Tên sản phẩm nổi bật", "price": "199.000₫", "discount": "-20% HÔM NAY", "cta": "🛍 Chốt ngay trên TikTok Shop", "image": "assets/vitamin_c.png", "delay": 1800, "sfx": "special" },
    { "id": "m4", "sender": "customer", "type": "text", "content": "...", "delay": 1400, "sfx": "ting" },
    { "id": "m5", "sender": "owner", "type": "text", "content": "...", "delay": 1400, "sfx": "pop" },
    { "id": "m6", "sender": "owner", "type": "like_sticker", "content": "👍", "delay": 800, "sfx": "pop" }
  ]
}`;

        const models = ['gemini-2.5-flash', 'gemini-2.0-flash'];
        let responseData = null;
        let lastErr = '';

        for (const model of models) {
            const resp = await fetch(
                `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(apiKey)}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        contents: [{ parts: [{ text: prompt }] }],
                        generationConfig: { temperature: 0.9, responseMimeType: 'application/json' }
                    })
                }
            );
            if (resp.ok) {
                responseData = await resp.json();
                break;
            }
            const errTxt = await resp.text();
            lastErr = `HTTP ${resp.status}: ${errTxt.slice(0, 180)}`;
            if (resp.status !== 404) break;
        }

        if (!responseData) {
            throw new Error(lastErr || 'Không thể kết nối Gemini API');
        }

        const rawText = responseData?.candidates?.[0]?.content?.parts?.[0]?.text || '';
        const cleaned = rawText.replace(/^```json\s*/i, '').replace(/```\s*$/i, '').trim();
        const generated = JSON.parse(cleaned);
        if (!generated || !Array.isArray(generated.messages) || generated.messages.length === 0) {
            throw new Error('AI không trả về danh sách messages hợp lệ.');
        }

        // Chuẩn hóa tin nhắn & đảm bảo senderId khớp nhân vật
        generated.theme = aiMode === 'group' ? 'group_messenger' : 'messenger_ios';
        generated.messages = generated.messages.map((m, idx) => ({
            id: m.id || `aimsg_${Date.now()}_${idx}`,
            senderId: m.senderId,
            senderName: m.senderName,
            sender: m.sender === 'owner' ? 'owner' : 'customer',
            type: m.type || 'text',
            content: m.content || '',
            price: m.price,
            discount: m.discount,
            cta: m.cta,
            image: m.image,
            delay: Number(m.delay) || 1500,
            sfx: m.sfx || (m.sender === 'customer' ? 'ting' : 'pop')
        }));

        const newKey = 'scenario_ai_' + Date.now();
        scenarios[newKey] = generated;
        saveScenariosToStorage();
        openScenarioFromCard(newKey);
        renderScenarioCards();
        document.getElementById('ai-generator-box').style.display = 'none';
        showToast(`✨ AI đã tạo xong kịch bản "${generated.title}"!`, 'success');
    } catch (err) {
        console.error('[AI Generator]', err);
        showToast('⚠️ Lỗi tạo bằng AI: ' + err.message, 'error', 5000);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
    }
}

// ============================================================================
// 3. TRÌNH SOẠN THẢO TRỰC QUAN (SCRIPT BUILDER ENGINE)
// ============================================================================
function getScenarioParticipants(scenarioData) {
    const owner = characterRoster.find(c => c.id === scenarioData?.ownerCharId)
        || characterRoster.find(c => c.role === 'owner')
        || characterRoster[0]
        || defaultCharacters[0];
    const customer = characterRoster.find(c => c.id === scenarioData?.customerCharId)
        || characterRoster.find(c => c.role === 'customer')
        || characterRoster[1]
        || characterRoster[0]
        || defaultCharacters[1];
    return { owner, customer };
}

function updateBuilderParticipantDropdowns() {
    const selectOwner = document.getElementById('select-builder-owner');
    const selectCust = document.getElementById('select-builder-customer');
    if (!selectOwner || !selectCust) return;

    selectOwner.innerHTML = '';
    selectCust.innerHTML = '';

    characterRoster.forEach(char => {
        const opt = document.createElement('option');
        opt.value = char.id;
        opt.textContent = `${char.role === 'owner' ? '👑' : '💬'} ${char.name}`;
        if (char.role === 'owner') {
            selectOwner.appendChild(opt.cloneNode(true));
        } else {
            selectCust.appendChild(opt.cloneNode(true));
        }
    });

    if (selectOwner.children.length === 0 || selectCust.children.length === 0) {
        characterRoster.forEach(char => {
            const opt = document.createElement('option');
            opt.value = char.id;
            opt.textContent = char.name;
            selectOwner.appendChild(opt.cloneNode(true));
            selectCust.appendChild(opt.cloneNode(true));
        });
    }

    const currentData = scenarios[currentScenarioKey];
    if (currentData) {
        const { owner, customer } = getScenarioParticipants(currentData);
        selectOwner.value = owner.id;
        selectCust.value = customer.id;
    }
}

function renderScriptBuilder() {
    const data = scenarios[currentScenarioKey];
    if (!data) return;

    const titleInput = document.getElementById('builder-scenario-title');
    if (titleInput) titleInput.value = data.title || '';

    updateBuilderParticipantDropdowns();

    const container = document.getElementById('builder-dialogue-list');
    if (!container) return;
    container.innerHTML = '';

    const { owner, customer } = getScenarioParticipants(data);
    const isGroup = data.theme === 'group_messenger' || currentStudioMode === 'group';

    data.messages.forEach((msg, index) => {
        const matchedChar = isGroup
            ? (characterRoster.find(c => c.id === msg.senderId) || characterRoster.find(c => c.name === msg.senderName))
            : null;
        const effectiveRole = matchedChar ? matchedChar.role : msg.sender;
        const isCust = effectiveRole === 'customer';
        const card = document.createElement('div');
        card.className = `dialogue-card ${isCust ? 'left-bubble' : 'right-bubble'}`;
        card.id = `line-card-${index}`;

        let senderSelectHtml = '';
        if (isGroup) {
            const curSenderId = msg.senderId || (msg.sender === 'owner' ? owner.id : customer.id);
            senderSelectHtml = `<select class="dialogue-sender-select" onchange="changeGroupLineSender(${index}, this.value)">`;
            characterRoster.forEach(c => {
                const isSel = (c.id === curSenderId || c.name === msg.senderName);
                senderSelectHtml += `<option value="${escapeHtml(c.id)}" ${isSel ? 'selected' : ''}>👤 ${escapeHtml(c.name)}</option>`;
            });
            senderSelectHtml += `</select>`;
        } else {
            senderSelectHtml = `
                <select class="dialogue-sender-select" onchange="changeLineSender(${index}, this.value)">
                    <option value="customer" ${isCust ? 'selected' : ''}>💬 Khách: ${escapeHtml(customer.name)}</option>
                    <option value="owner" ${!isCust ? 'selected' : ''}>👑 Tiệm: ${escapeHtml(owner.name)}</option>
                </select>
            `;
        }

        let html = `
            <div class="dialogue-header">
                ${senderSelectHtml}
                <div class="dialogue-actions">
                    ${index > 0 ? `<button type="button" class="btn-mini" onclick="moveLineUp(${index})" title="Đẩy lên">⬆️</button>` : ''}
                    ${index < data.messages.length - 1 ? `<button type="button" class="btn-mini" onclick="moveLineDown(${index})" title="Đẩy xuống">⬇️</button>` : ''}
                    <button type="button" class="btn-mini delete" onclick="deleteLine(${index})" title="Xóa câu nói này">✕</button>
                </div>
            </div>

            <div class="dialogue-type-tabs">
                <button type="button" class="type-btn ${msg.type === 'text' ? 'active' : ''}" onclick="changeLineType(${index}, 'text')">💬 Lời thoại</button>
                <button type="button" class="type-btn ${msg.type === 'product_card' || msg.type === 'product' ? 'active' : ''}" onclick="changeLineType(${index}, 'product_card')">📦 Thẻ sản phẩm Shop</button>
                <button type="button" class="type-btn ${msg.type === 'like_sticker' || msg.type === 'sticker' ? 'active' : ''}" onclick="changeLineType(${index}, 'like_sticker')">👍 Sticker Like Bự</button>
            </div>
        `;

        if (msg.type === 'text') {
            html += `
                <textarea class="input-field" rows="2" style="font-size:13px;" placeholder="Nhập nội dung tin nhắn thoại..." oninput="updateLineContent(${index}, 'content', this.value)">${escapeHtml(msg.content || '')}</textarea>
            `;
        } else if (msg.type === 'product_card' || msg.type === 'product') {
            html += `
                <div class="product-form-fields">
                    <input type="text" class="input-field" placeholder="Tên sản phẩm..." value="${escapeHtml(msg.content || '')}" oninput="updateLineContent(${index}, 'content', this.value)">
                    <div style="display:flex;gap:6px;">
                        <input type="text" class="input-field" placeholder="Giá tiền (e.g. 99.000₫)" value="${escapeHtml(msg.price || '')}" oninput="updateLineContent(${index}, 'price', this.value)">
                        <input type="text" class="input-field" placeholder="Huy hiệu SALE (e.g. -20% HOT)" value="${escapeHtml(msg.discount || '')}" oninput="updateLineContent(${index}, 'discount', this.value)">
                    </div>
                </div>
            `;
        } else if (msg.type === 'like_sticker' || msg.type === 'sticker') {
            html += `
                <div style="padding:6px; font-size:13px; color:#60a5fa; font-weight:600; display:flex; align-items:center; gap:8px;">
                    <span style="font-size:24px;">👍</span> Nhân vật sẽ thả Sticker Nút Like Bự chuẩn Facebook Messenger!
                </div>
            `;
        }

        card.innerHTML = html;
        container.appendChild(card);
    });
}

let _saveScenarioDebounce = null;
function scheduleSaveScenarios() {
    if (_saveScenarioDebounce) clearTimeout(_saveScenarioDebounce);
    _saveScenarioDebounce = setTimeout(() => {
        saveScenariosToStorage();
    }, 350);
}

function changeLineSender(index, sender) {
    scenarios[currentScenarioKey].messages[index].sender = sender;
    scenarios[currentScenarioKey].messages[index].sfx = sender === 'customer' ? 'ting' : 'pop';
    saveScenariosToStorage();
    renderScriptBuilder();
}

function changeLineType(index, type) {
    const msg = scenarios[currentScenarioKey].messages[index];
    msg.type = type;
    if (type === 'like_sticker') {
        msg.content = '👍';
    } else if (type === 'product_card' && !msg.price) {
        msg.content = 'Vitamin C Kháng Mỏi Siêu HOT';
        msg.price = '99.000₫';
        msg.discount = '-20% SALE';
        msg.image = 'assets/vitamin_c.png';
        msg.cta = '🛍 Chốt ngay trên TikTok Shop';
        msg.sfx = 'special';
    }
    saveScenariosToStorage();
    renderScriptBuilder();
}

function updateLineContent(index, field, value) {
    scenarios[currentScenarioKey].messages[index][field] = value;
    scheduleSaveScenarios();
}

function deleteLine(index) {
    if (scenarios[currentScenarioKey].messages.length <= 1) {
        showToast('⚠️ Kịch bản cần có ít nhất 1 câu tin nhắn!', 'warn');
        return;
    }
    scenarios[currentScenarioKey].messages.splice(index, 1);
    saveScenariosToStorage();
    renderScriptBuilder();
}

function moveLineUp(index) {
    if (index > 0) {
        const msgs = scenarios[currentScenarioKey].messages;
        [msgs[index - 1], msgs[index]] = [msgs[index], msgs[index - 1]];
        saveScenariosToStorage();
        renderScriptBuilder();
    }
}

function moveLineDown(index) {
    const msgs = scenarios[currentScenarioKey].messages;
    if (index < msgs.length - 1) {
        [msgs[index], msgs[index + 1]] = [msgs[index + 1], msgs[index]];
        saveScenariosToStorage();
        renderScriptBuilder();
    }
}

function addNewLineToScript() {
    const data = scenarios[currentScenarioKey];
    if (!data) return;
    const isGroup = data.theme === 'group_messenger' || currentStudioMode === 'group';
    const lastMsg = data.messages[data.messages.length - 1];
    const lastSender = lastMsg ? lastMsg.sender : 'owner';
    const nextSender = lastSender === 'customer' ? 'owner' : 'customer';

    const newMsg = {
        id: 'msg_' + Date.now(),
        sender: nextSender,
        type: 'text',
        content: nextSender === 'customer' ? 'Shop ơi cho em đặt thêm 1 combo nữa nhé!' : 'Dạ vâng chốt đơn ngay cho bạn ạ! 💚',
        delay: 1500,
        sfx: nextSender === 'customer' ? 'ting' : 'pop'
    };

    if (isGroup) {
        const targetChar = nextSender === 'owner'
            ? (characterRoster.find(c => c.role === 'owner') || characterRoster[0])
            : (characterRoster.find(c => c.role === 'customer') || characterRoster[1] || characterRoster[0]);
        if (targetChar) {
            newMsg.senderId = targetChar.id;
            newMsg.senderName = targetChar.name;
            newMsg.sender = targetChar.role || nextSender;
        }
    }

    data.messages.push(newMsg);
    saveScenariosToStorage();
    renderScriptBuilder();
    setTimeout(() => {
        const list = document.getElementById('builder-dialogue-list');
        if (list) list.scrollTop = list.scrollHeight;
    }, 100);
}

function createNewCustomScenario() {
    const newKey = 'scenario_custom_' + Date.now();
    const isGroupMode = currentStudioMode === 'group';
    const owner = characterRoster.find(c => c.role === 'owner') || characterRoster[0];
    const cust = characterRoster.find(c => c.role === 'customer') || characterRoster[1] || characterRoster[0];

    if (isGroupMode) {
        scenarios[newKey] = {
            title: '🏢 Kịch bản Group Chat mới của bạn',
            desc: 'Kịch bản nhóm chat nhiều nhân vật tự soạn.',
            theme: 'group_messenger',
            groupName: groupChatSettings.name || 'Nhóm Chat Mới',
            groupUnread: groupChatSettings.unread ?? 8,
            groupAvatar: groupChatSettings.avatar || 'assets/steel_door_logo.png',
            bgWallpaper: groupChatSettings.wallpaper || 'assets/bg_anime_sky.jpg',
            bubbleColor: groupChatSettings.bubbleColor || '#e0f2fe',
            messages: [
                {
                    id: 'gmsg_1',
                    senderId: owner.id,
                    senderName: owner.name,
                    sender: 'owner',
                    type: 'text',
                    content: 'Mọi người ơi! Đơn hàng hôm nay chuẩn bị tới đâu rồi?',
                    delay: 1500,
                    sfx: 'pop'
                },
                {
                    id: 'gmsg_2',
                    senderId: cust.id,
                    senderName: cust.name,
                    sender: 'customer',
                    type: 'text',
                    content: 'Dạ xong hết rồi ạ, chuẩn bị giao cho khách VIP luôn!',
                    delay: 1500,
                    sfx: 'ting'
                }
            ]
        };
    } else {
        scenarios[newKey] = {
            title: '✨ Kịch bản Chat 1-1 mới của bạn',
            desc: 'Kịch bản tùy biến cá nhân hóa với sự góp mặt của dàn nhân vật riêng.',
            theme: 'messenger_ios',
            ownerCharId: owner.id,
            customerCharId: cust.id,
            messages: [
                {
                    id: 'msg_1',
                    sender: 'customer',
                    type: 'text',
                    content: 'Chào Shop! Cho hỏi bên mình có sản phẩm mới không ạ? 😄',
                    delay: 1400,
                    sfx: 'ting'
                },
                {
                    id: 'msg_2',
                    sender: 'owner',
                    type: 'text',
                    content: 'Dạ có ngay! Mời bạn xem qua mẫu siêu HOT bên mình nhé... ⚡',
                    delay: 1600,
                    sfx: 'pop'
                }
            ]
        };
    }

    saveScenariosToStorage();
    selectScenario(newKey);
    renderScenarioCards();
    switchTab('builder');
    showToast('🎉 Đã tạo kịch bản mới! Hãy chỉnh sửa lời thoại bên dưới.', 'success');
}

function applyScriptBuilderToStage() {
    const sc = scenarios[currentScenarioKey];
    if (!sc) return;

    const titleInput = document.getElementById('builder-scenario-title');
    const selectOwner = document.getElementById('select-builder-owner');
    const selectCust = document.getElementById('select-builder-customer');

    if (titleInput && titleInput.value.trim()) {
        sc.title = titleInput.value.trim();
    }
    if (sc.theme !== 'group_messenger') {
        if (selectOwner && selectOwner.value) {
            sc.ownerCharId = selectOwner.value;
        }
        if (selectCust && selectCust.value) {
            sc.customerCharId = selectCust.value;
        }
    }

    saveScenariosToStorage();
    renderScenarioCards();
    refreshCurrentStageDisplay();

    const jsonEditor = document.getElementById('json-editor');
    if (jsonEditor) jsonEditor.value = JSON.stringify(sc, null, 2);

    showToast('✨ Đã áp dụng & lưu kịch bản lên màn hình!', 'success');
}

function renderAllMessagesInstant() {
    const data = scenarios[currentScenarioKey];
    if (!data || !data.messages) return;

    data.messages.forEach(msg => {
        appendMessage(msg);
    });

    const chatWindow = document.getElementById('chat-window');
    const groupWindow = document.getElementById('group-chat-window');
    if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;
    if (groupWindow) groupWindow.scrollTop = groupWindow.scrollHeight;
}


// ============================================================================
// 4. TẦNG ÂM THANH (WEB AUDIO + RECORDING STREAM + EDGE-TTS / CUSTOM AUDIO)
// ============================================================================
let isPlaying = false;
let playbackSessionId = 0;
let activePlaybackTimers = new Set();
let activeTypingInterval = null;
let activeAudioEl = null;

let audioCtx = null;
let mediaAudioDest = null;
let synth = window.speechSynthesis || null;
let voices = [];

function initAudio() {
    const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
    if (!audioCtx && AudioCtxClass) {
        audioCtx = new AudioCtxClass();
        if (typeof audioCtx.createMediaStreamDestination === 'function') {
            mediaAudioDest = audioCtx.createMediaStreamDestination();
        }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume().catch(() => {});
    }
    if (synth && voices.length === 0) {
        voices = synth.getVoices();
    }
}

window.getStudioAudioStream = function () {
    return mediaAudioDest ? mediaAudioDest.stream : null;
};

if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = () => {
        voices = window.speechSynthesis.getVoices();
    };
}

function schedulePlaybackTimer(fn, ms) {
    const id = setTimeout(() => {
        activePlaybackTimers.delete(id);
        fn();
    }, ms);
    activePlaybackTimers.add(id);
    return id;
}

function stopAllPlayback() {
    playbackSessionId++;
    isPlaying = false;
    activePlaybackTimers.forEach(id => clearTimeout(id));
    activePlaybackTimers.clear();
    if (activeTypingInterval) {
        clearInterval(activeTypingInterval);
        activeTypingInterval = null;
    }
    if (activeAudioEl) {
        try {
            activeAudioEl.pause();
            activeAudioEl.src = '';
        } catch (e) { /* ignore */ }
        activeAudioEl = null;
    }
    if (synth) {
        try {
            synth.cancel();
        } catch (e) { /* ignore */ }
    }
}

function playSFX(type) {
    const sfxEnabled = document.getElementById('toggle-sfx')?.checked;
    if (!sfxEnabled || !audioCtx) return;

    if (audioCtx.state === 'suspended') {
        audioCtx.resume().catch(() => {});
    }

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    if (mediaAudioDest) {
        gain.connect(mediaAudioDest);
    }

    const now = audioCtx.currentTime;

    if (type === 'ting') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(800, now);
        osc.frequency.exponentialRampToValueAtTime(1200, now + 0.1);
        gain.gain.setValueAtTime(0.3, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
        osc.start(now);
        osc.stop(now + 0.15);
    } else if (type === 'pop') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(350, now);
        osc.frequency.exponentialRampToValueAtTime(600, now + 0.08);
        gain.gain.setValueAtTime(0.35, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
        osc.start(now);
        osc.stop(now + 0.1);
    } else if (type === 'special') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(523.25, now);
        osc.frequency.setValueAtTime(659.25, now + 0.1);
        osc.frequency.setValueAtTime(783.99, now + 0.2);
        gain.gain.setValueAtTime(0.4, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.4);
        osc.start(now);
        osc.stop(now + 0.4);
    }
}

function _playHtmlAudio(url, sessionId, revokeAfter, onDone) {
    if (sessionId !== playbackSessionId) {
        if (revokeAfter) URL.revokeObjectURL(url);
        return;
    }

    if (activeAudioEl) {
        try {
            activeAudioEl.pause();
        } catch (e) { /* ignore */ }
    }

    const audio = new Audio(url);
    activeAudioEl = audio;

    // Kết nối với Web Audio API Destination để luồng ghi hình WebM thu được âm thanh
    if (audioCtx && mediaAudioDest) {
        try {
            const srcNode = audioCtx.createMediaElementSource(audio);
            srcNode.connect(audioCtx.destination);
            srcNode.connect(mediaAudioDest);
        } catch (e) {
            // Nếu môi trường hạn chế MediaElementSource thì vẫn phát trực tiếp qua HTMLAudio
        }
    }

    let finished = false;
    const finalize = () => {
        if (finished) return;
        finished = true;
        if (activeAudioEl === audio) activeAudioEl = null;
        if (revokeAfter) {
            setTimeout(() => URL.revokeObjectURL(url), 500);
        }
        if (sessionId === playbackSessionId && onDone) onDone();
    };

    audio.addEventListener('ended', finalize, { once: true });
    audio.addEventListener('error', finalize, { once: true });
    audio.play().catch(finalize);
}

function _speakWebSpeechFallback(text, pitch, sessionId, callback) {
    if (sessionId !== playbackSessionId) return;
    if (!synth || typeof SpeechSynthesisUtterance === 'undefined') {
        schedulePlaybackTimer(() => {
            if (sessionId === playbackSessionId && callback) callback();
        }, Math.max(900, Math.min(3500, text.length * 60)));
        return;
    }

    synth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const viVoice = voices.find(v =>
        v.lang.includes('vi') ||
        v.name.includes('Vietnamese') ||
        v.name.includes('HoaiMy') ||
        v.name.includes('NamMinh')
    );
    if (viVoice) utterance.voice = viVoice;
    utterance.pitch = Number(pitch) || 1.0;
    utterance.rate = 1.0;

    let called = false;
    const done = () => {
        if (called) return;
        called = true;
        if (sessionId === playbackSessionId && callback) callback();
    };

    utterance.onend = done;
    utterance.onerror = done;
    synth.speak(utterance);

    const estimatedDuration = Math.max(1500, text.length * 75);
    schedulePlaybackTimer(() => {
        if (!called) done();
    }, estimatedDuration + 900);
}

async function speakText(text, speakerOrPitch = 1.0, callback, sessionId = playbackSessionId) {
    const ttsEnabled = document.getElementById('toggle-tts')?.checked;
    const trimmed = String(text || '').trim();
    if (!ttsEnabled || !trimmed || trimmed === '👍') {
        schedulePlaybackTimer(() => {
            if (sessionId === playbackSessionId && callback) callback();
        }, 500);
        return;
    }

    const isObj = speakerOrPitch && typeof speakerOrPitch === 'object';
    const speaker = isObj ? speakerOrPitch : null;
    const pitch = isObj ? (speaker.pitch || 1.0) : (Number(speakerOrPitch) || 1.0);
    const voice = speaker ? inferDefaultVoice(speaker) : (pitch >= 1.22 ? 'vi-VN-HoaiMyNeural' : 'vi-VN-NamMinhNeural');

    // 1. Ưu tiên giọng thu âm riêng nếu nhân vật có gắn
    if (speaker && speaker.customVoiceDataUrl) {
        _playHtmlAudio(speaker.customVoiceDataUrl, sessionId, false, callback);
        return;
    }

    // 2. Nếu có Local Server -> gọi /api/tts để lấy giọng Neural Edge-TTS sắc nét
    if (serverAvailable) {
        try {
            const resp = await fetch('/api/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: trimmed, voice, rate: '+0%' })
            });
            if (sessionId !== playbackSessionId) return;
            if (resp.ok) {
                const blob = await resp.blob();
                if (blob && blob.size > 400) {
                    const objUrl = URL.createObjectURL(blob);
                    _playHtmlAudio(objUrl, sessionId, true, callback);
                    return;
                }
            }
        } catch (err) {
            console.warn('[TTS Server Fallback]', err);
        }
    }

    // 3. Fallback sang Web Speech API trên trình duyệt
    _speakWebSpeechFallback(trimmed, pitch, sessionId, callback);
}


// ============================================================================
// 5. HIỂN THỊ GIAO DIỆN MÀN HÌNH CHAT 1-1 / GROUP CHAT & TIMELINE DEMO
// ============================================================================
function renderPhoneHeader() {
    const data = scenarios[currentScenarioKey];
    if (!data) return;

    const { owner } = getScenarioParticipants(data);
    const headerAvatar = document.querySelector('.messenger-header .avatar');
    const headerName = document.querySelector('.messenger-header .name');

    if (headerAvatar) headerAvatar.src = owner.avatar || 'assets/owner_avatar.png';
    if (headerName) headerName.textContent = owner.name;
}

function refreshCurrentStageDisplay() {
    const data = scenarios[currentScenarioKey];
    const isGroup = currentStudioMode === 'group' || data?.theme === 'group_messenger';
    if (isGroup) {
        renderGroupHeader();
    } else {
        renderPhoneHeader();
    }
    resetChat();
    renderAllMessagesInstant();
}

const THUMBS_UP_SVG = `<svg viewBox="0 0 24 24"><path d="M2.3 10.5c0-.83.67-1.5 1.5-1.5h1.7c.83 0 1.5.67 1.5 1.5v9c0 .83-.67 1.5-1.5 1.5H3.8c-.83 0-1.5-.67-1.5-1.5v-9z M8.5 19.5V10.8l2.9-4.2c.4-.6 1.1-1.1 1.8-1.4.5-.2 1.1-.2 1.5.1.5.3.8.9.8 1.5v3.2h3.3c1.7 0 3.1 1.3 3.2 3 .1.9-.3 1.7-.9 2.3.4.6.4 1.4.1 2.1-.3.6-.8 1-1.3 1.2.3.5.3 1.2 0 1.8-.4.7-1.1 1.1-1.9 1.1H11c-1.4 0-2.5-1.1-2.5-2.5z"/></svg>`;
const SEND_ARROW_SVG = `<svg viewBox="0 0 24 24"><path d="M3.4 20.4l17.4-7.8c.8-.4.8-1.5 0-1.8L3.4 3.1c-.8-.3-1.6.4-1.4 1.3L3.7 11c.1.3.4.6.7.6h7.1c.4 0 .7.3.7.7s-.3.7-.7.7H4.4c-.4 0-.7.2-.7.6L2 19.1c-.2.9.6 1.6 1.4 1.3z"/></svg>`;

function setSendButtonIcon(isTyping) {
    const sendBtn = document.getElementById('send-btn');
    if (!sendBtn) return;
    sendBtn.innerHTML = isTyping ? SEND_ARROW_SVG : THUMBS_UP_SVG;
}

function resetChat() {
    stopAllPlayback();

    const chatWindow = document.getElementById('chat-window');
    const groupWindow = document.getElementById('group-chat-window');
    if (groupWindow) {
        groupWindow.innerHTML = '';
    }

    const data = scenarios[currentScenarioKey];
    if (data && chatWindow) {
        const { owner, customer } = getScenarioParticipants(data);

        chatWindow.innerHTML = `
            <div class="chat-intro-banner">
                <img class="intro-avatar" src="${escapeHtml(owner.avatar || 'assets/owner_avatar.png')}" alt="Avatar" onerror="this.src='assets/owner_avatar.png'">
                <div class="intro-name">${escapeHtml(owner.name)}</div>
                <div class="intro-sub">Các bạn là bạn bè trên Facebook • Tài khoản kinh doanh</div>
                <div class="intro-time-divider">Hôm nay 22:30</div>
            </div>
        `;

        const typingRow = document.createElement('div');
        typingRow.className = 'typing-indicator-row';
        typingRow.id = 'typing-indicator';
        typingRow.innerHTML = `
            <img class="avatar-small" src="${escapeHtml(customer.avatar || 'assets/customer_avatar.png')}" alt="Avatar" onerror="this.src='assets/customer_avatar.png'">
            <div class="typing-bubble">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chatWindow.appendChild(typingRow);

        const seenRow = document.createElement('div');
        seenRow.className = 'seen-indicator';
        seenRow.id = 'seen-indicator';
        seenRow.innerHTML = `
            <span class="seen-text" id="seen-status-text">Đã xem</span>
            <img class="seen-avatar-tiny" src="${escapeHtml(customer.avatar || 'assets/customer_avatar.png')}" alt="Seen" onerror="this.src='assets/customer_avatar.png'">
        `;
        chatWindow.appendChild(seenRow);
    }

    const inputText = document.getElementById('input-text');
    if (inputText) {
        inputText.textContent = 'Aa';
        inputText.classList.add('empty');
    }
    setSendButtonIcon(false);

    const btnPlay = document.getElementById('btn-play');
    if (btnPlay) {
        btnPlay.innerHTML = '▶ Bắt Đầu Phát Demo (Auto Play)';
        btnPlay.classList.remove('playing');
    }
}

function typeInInput(text, duration, callback) {
    if (text === '👍') {
        if (callback) schedulePlaybackTimer(callback, 300);
        return;
    }

    const inputText = document.getElementById('input-text');
    if (!inputText) {
        if (callback) callback();
        return;
    }

    if (activeTypingInterval) clearInterval(activeTypingInterval);
    inputText.classList.remove('empty');
    inputText.textContent = '';
    setSendButtonIcon(true);

    let i = 0;
    const len = Math.max(1, text.length);
    const intervalTime = Math.max(10, Math.min(25, (duration * 0.7) / len));
    activeTypingInterval = setInterval(() => {
        if (i < text.length) {
            inputText.textContent += text[i];
            i++;
        } else {
            clearInterval(activeTypingInterval);
            activeTypingInterval = null;
            schedulePlaybackTimer(() => {
                inputText.textContent = 'Aa';
                inputText.classList.add('empty');
                setSendButtonIcon(false);
                if (callback) callback();
            }, 250);
        }
    }, intervalTime);
}

function appendMessage(msg) {
    if (!msg) return;

    if (currentStudioMode === 'group') {
        const groupWindow = document.getElementById('group-chat-window');
        if (!groupWindow) return;

        const char = characterRoster.find(c => c.id === msg.senderId)
            || characterRoster.find(c => c.name === msg.senderName)
            || characterRoster[0];

        const senderName = msg.senderName || char?.name || 'Thành viên';
        const avatar = char?.avatar || 'assets/customer_avatar.png';

        const row = document.createElement('div');
        row.className = 'group-message-row';

        let bubbleHtml = '';
        if (msg.type === 'text') {
            bubbleHtml = `<div class="bubble-group-pink">${escapeHtml(msg.content)}</div>`;
        } else if (msg.type === 'product_card' || msg.type === 'product') {
            bubbleHtml = `
                <div class="bubble bubble-product">
                    <div class="product-image-container">
                        <img src="${escapeHtml(msg.image || 'assets/vitamin_c.png')}" alt="Product" onerror="this.src='assets/vitamin_c.png'">
                        <span class="product-badge">${escapeHtml(msg.discount || 'SIÊU HOT')}</span>
                    </div>
                    <div class="product-meta-box">
                        <span class="product-shop-tag">TIKTOK SHOP • MUA NGAY KẺO HẾT</span>
                        <div class="product-title">${escapeHtml(msg.content)}</div>
                        <div class="product-price-row">
                            <span class="product-price">${escapeHtml(msg.price || '99.000₫')}</span>
                        </div>
                        <button type="button" class="product-cta-btn">${escapeHtml(msg.cta || '🛍 Xem Cửa Hàng / Chốt Đơn')}</button>
                    </div>
                </div>
            `;
        } else if (msg.type === 'like_sticker' || msg.type === 'sticker') {
            bubbleHtml = `
                <div class="bubble-sticker-like" style="justify-content: flex-start;">
                    <svg viewBox="0 0 24 24"><path d="M2.3 10.5c0-.83.67-1.5 1.5-1.5h1.7c.83 0 1.5.67 1.5 1.5v9c0 .83-.67 1.5-1.5 1.5H3.8c-.83 0-1.5-.67-1.5-1.5v-9z M8.5 19.5V10.8l2.9-4.2c.4-.6 1.1-1.1 1.8-1.4.5-.2 1.1-.2 1.5.1.5.3.8.9.8 1.5v3.2h3.3c1.7 0 3.1 1.3 3.2 3 .1.9-.3 1.7-.9 2.3.4.6.4 1.4.1 2.1-.3.6-.8 1-1.3 1.2.3.5.3 1.2 0 1.8-.4.7-1.1 1.1-1.9 1.1H11c-1.4 0-2.5-1.1-2.5-2.5z"/></svg>
                </div>
            `;
        }

        row.innerHTML = `
            <img class="group-avatar-small" src="${escapeHtml(avatar)}" alt="${escapeHtml(senderName)}" onerror="this.src='assets/customer_avatar.png'">
            <div class="group-message-body">
                <div class="group-sender-name">${escapeHtml(senderName)}</div>
                ${bubbleHtml}
            </div>
        `;

        groupWindow.appendChild(row);
        groupWindow.scrollTop = groupWindow.scrollHeight;
        return;
    }

    const data = scenarios[currentScenarioKey];
    const chatWindow = document.getElementById('chat-window');
    const typingIndicator = document.getElementById('typing-indicator');
    const seenIndicator = document.getElementById('seen-indicator');
    if (!data || !chatWindow || !typingIndicator) return;

    if (seenIndicator) seenIndicator.classList.remove('active');

    const { customer } = getScenarioParticipants(data);
    const isCustomer = msg.sender === 'customer';
    const row = document.createElement('div');
    row.className = `message-row ${isCustomer ? 'left' : 'right'}`;

    const avatarHtml = isCustomer
        ? `<img class="avatar-small" src="${escapeHtml(customer.avatar || 'assets/customer_avatar.png')}" alt="Avatar" onerror="this.src='assets/customer_avatar.png'">`
        : '';
    let bubbleHtml = '';

    if (msg.type === 'text') {
        bubbleHtml = `<div class="bubble">${escapeHtml(msg.content)}</div>`;
    } else if (msg.type === 'product_card' || msg.type === 'product') {
        bubbleHtml = `
            <div class="bubble bubble-product">
                <div class="product-image-container">
                    <img src="${escapeHtml(msg.image || 'assets/vitamin_c.png')}" alt="Product" onerror="this.src='assets/vitamin_c.png'">
                    <span class="product-badge">${escapeHtml(msg.discount || 'SIÊU HOT')}</span>
                </div>
                <div class="product-meta-box">
                    <span class="product-shop-tag">TIKTOK SHOP • MUA NGAY KẺO HẾT</span>
                    <div class="product-title">${escapeHtml(msg.content)}</div>
                    <div class="product-price-row">
                        <span class="product-price">${escapeHtml(msg.price || '99.000₫')}</span>
                    </div>
                    <button type="button" class="product-cta-btn">${escapeHtml(msg.cta || '🛍 Xem Cửa Hàng / Chốt Đơn')}</button>
                </div>
            </div>
        `;
    } else if (msg.type === 'like_sticker' || msg.type === 'sticker') {
        bubbleHtml = `
            <div class="bubble-sticker-like">
                <svg viewBox="0 0 24 24"><path d="M2.3 10.5c0-.83.67-1.5 1.5-1.5h1.7c.83 0 1.5.67 1.5 1.5v9c0 .83-.67 1.5-1.5 1.5H3.8c-.83 0-1.5-.67-1.5-1.5v-9z M8.5 19.5V10.8l2.9-4.2c.4-.6 1.1-1.1 1.8-1.4.5-.2 1.1-.2 1.5.1.5.3.8.9.8 1.5v3.2h3.3c1.7 0 3.1 1.3 3.2 3 .1.9-.3 1.7-.9 2.3.4.6.4 1.4.1 2.1-.3.6-.8 1-1.3 1.2.3.5.3 1.2 0 1.8-.4.7-1.1 1.1-1.9 1.1H11c-1.4 0-2.5-1.1-2.5-2.5z"/></svg>
            </div>
        `;
    }

    row.innerHTML = avatarHtml + bubbleHtml;
    chatWindow.insertBefore(row, typingIndicator);

    if (!isCustomer && seenIndicator) {
        const statusText = document.getElementById('seen-status-text');
        if (statusText) {
            statusText.textContent = (msg.type === 'like_sticker' || msg.type === 'sticker') ? 'Đã gửi' : 'Đã xem';
        }
        if (document.body.classList.contains('no-chat-anim')) {
            seenIndicator.classList.add('active');
        } else {
            schedulePlaybackTimer(() => {
                if (seenIndicator) seenIndicator.classList.add('active');
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }, 350);
        }
    }

    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function runScenario() {
    const btnPlay = document.getElementById('btn-play');
    if (isPlaying) {
        stopAllPlayback();
        if (btnPlay) {
            btnPlay.innerHTML = '▶ Tiếp Tục Phát';
            btnPlay.classList.remove('playing');
        }
        return;
    }

    initAudio();

    const data = scenarios[currentScenarioKey];
    if (!data || !Array.isArray(data.messages) || data.messages.length === 0) return;

    const messages = data.messages;
    const { owner, customer } = getScenarioParticipants(data);

    const selector = currentStudioMode === 'group' ? '#group-chat-window .group-message-row' : '#chat-window .message-row';
    let index = document.querySelectorAll(selector).length;

    if (index >= messages.length) {
        resetChat();
        index = 0;
    }

    playbackSessionId++;
    const sessionId = playbackSessionId;
    isPlaying = true;

    if (btnPlay) {
        btnPlay.innerHTML = '⏸ Tạm Dừng Demo';
        btnPlay.classList.add('playing');
    }

    function playNext() {
        if (!isPlaying || sessionId !== playbackSessionId) return;
        if (index >= messages.length) {
            isPlaying = false;
            if (btnPlay) {
                btnPlay.innerHTML = '🔄 Phát Lại Từ Đầu';
                btnPlay.classList.remove('playing');
            }
            return;
        }

        const msg = messages[index];

        if (currentStudioMode === 'group') {
            const speaker = characterRoster.find(c => c.id === msg.senderId)
                || characterRoster.find(c => c.name === msg.senderName)
                || (msg.sender === 'owner' ? owner : customer);
            const groupWin = document.getElementById('group-chat-window');
            if (groupWin) groupWin.scrollTop = groupWin.scrollHeight;

            schedulePlaybackTimer(() => {
                if (sessionId !== playbackSessionId || !isPlaying) return;
                appendMessage(msg);
                playSFX(msg.sfx || (msg.sender === 'customer' ? 'ting' : 'pop'));
                const spokenText = msg.type === 'product_card'
                    ? `${msg.content}. Giá chỉ ${msg.price || ''}.`
                    : msg.content;
                speakText(spokenText, speaker, () => {
                    if (sessionId !== playbackSessionId || !isPlaying) return;
                    index++;
                    schedulePlaybackTimer(playNext, 250);
                }, sessionId);
            }, msg.delay || 1200);
            return;
        }

        const isCustomer = msg.sender === 'customer';
        const speaker = isCustomer ? customer : owner;
        const chatWindow = document.getElementById('chat-window');
        const typingIndicator = document.getElementById('typing-indicator');

        if (isCustomer && typingIndicator && !document.body.classList.contains('hide-bottom-bar')) {
            typingIndicator.classList.add('active');
        }
        if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;

        const delayMs = msg.delay || (isCustomer ? 1200 : 1400);
        schedulePlaybackTimer(() => {
            if (sessionId !== playbackSessionId || !isPlaying) return;
            if (typingIndicator) typingIndicator.classList.remove('active');
            appendMessage(msg);
            playSFX(msg.sfx || (isCustomer ? 'ting' : 'pop'));

            const spokenText = msg.type === 'product_card'
                ? `${msg.content}. Giá chỉ ${msg.price || ''}.`
                : msg.content;

            speakText(spokenText, speaker, () => {
                if (sessionId !== playbackSessionId || !isPlaying) return;
                index++;
                schedulePlaybackTimer(playNext, 250);
            }, sessionId);
        }, delayMs);
    }

    playNext();
}

function selectScenario(key) {
    const sc = scenarios[key];
    if (!sc) return;
    currentScenarioKey = key;

    const expectedMode = sc.theme === 'group_messenger' ? 'group' : 'chat';
    if (currentStudioMode !== expectedMode) {
        currentStudioMode = expectedMode;
        syncModeButtonsAndPanels(expectedMode);
    }

    document.querySelectorAll('.scenario-card').forEach(card => card.classList.remove('active'));
    const selected = document.getElementById(`card-${key}`);
    if (selected) selected.classList.add('active');

    const jsonEditor = document.getElementById('json-editor');
    if (jsonEditor) jsonEditor.value = JSON.stringify(sc, null, 2);

    refreshCurrentStageDisplay();
    renderScriptBuilder();
}

function switchTab(tabName) {
    const tabCards = document.getElementById('view-cards');
    const tabBuilder = document.getElementById('view-builder');
    const tabChars = document.getElementById('view-characters');
    const tabJson = document.getElementById('view-json');

    const btnCards = document.getElementById('tab-btn-cards');
    const btnBuilder = document.getElementById('tab-btn-builder');
    const btnChars = document.getElementById('tab-btn-chars');
    const btnJson = document.getElementById('tab-btn-json');

    [tabCards, tabBuilder, tabChars, tabJson].forEach(el => { if (el) el.style.display = 'none'; });
    [btnCards, btnBuilder, btnChars, btnJson].forEach(el => { if (el) el.classList.remove('active'); });

    if (tabName === 'cards') {
        if (tabCards) tabCards.style.display = 'flex';
        if (btnCards) btnCards.classList.add('active');
        renderScenarioCards();
    } else if (tabName === 'builder') {
        if (tabBuilder) tabBuilder.style.display = 'flex';
        if (btnBuilder) btnBuilder.classList.add('active');
        renderScriptBuilder();
    } else if (tabName === 'characters') {
        if (tabChars) tabChars.style.display = 'flex';
        if (btnChars) btnChars.classList.add('active');
        renderCharacterRoster();
    } else if (tabName === 'json') {
        if (tabJson) tabJson.style.display = 'flex';
        if (btnJson) btnJson.classList.add('active');
        const jsonEditor = document.getElementById('json-editor');
        if (jsonEditor) jsonEditor.value = JSON.stringify(scenarios[currentScenarioKey], null, 2);
    }
}

function applyJsonChanges() {
    try {
        const raw = document.getElementById('json-editor').value;
        const parsed = JSON.parse(raw);
        const scObj = parsed.scenario && Array.isArray(parsed.scenario.messages) ? parsed.scenario : parsed;
        if (!scObj || !Array.isArray(scObj.messages)) {
            throw new Error('Kịch bản JSON bắt buộc phải có mảng "messages".');
        }

        scenarios[currentScenarioKey] = scObj;
        saveScenariosToStorage();

        const targetMode = scObj.theme === 'group_messenger' ? 'group' : 'chat';
        if (currentStudioMode !== targetMode) {
            currentStudioMode = targetMode;
            syncModeButtonsAndPanels(targetMode);
        }

        renderScenarioCards();
        renderScriptBuilder();
        refreshCurrentStageDisplay();
        showToast('🎉 Đã áp dụng & lưu kịch bản JSON lên màn hình!', 'success');
    } catch (e) {
        showToast('⚠️ Lỗi cú pháp JSON: ' + e.message, 'error', 4500);
    }
}


// ============================================================================
// 6. SERVER HEALTH CHECK & XUẤT BẢN CAPCUT (.ZIP) / VIDEO MP4 TRỰC TIẾP
// ============================================================================
async function checkServerHealth() {
    const badge = document.getElementById('server-status-badge');
    const hint = document.getElementById('server-export-hint');
    if (window.location.protocol === 'file:') {
        serverAvailable = false;
        return;
    }

    try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 2000);
        const resp = await fetch('/api/health', { cache: 'no-store', signal: controller.signal });
        clearTimeout(timer);
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const info = await resp.json();
        if (info && info.ok) {
            serverAvailable = true;
            serverCapabilities = info.capabilities || {};
            if (badge) {
                badge.className = 'server-pill online';
                badge.textContent = '🟢 Local Server Sẵn Sàng';
                badge.title = `FFmpeg: ${serverCapabilities.ffmpeg ? 'OK' : 'Thiếu'} | Edge-TTS: ${serverCapabilities.edge_tts ? 'OK' : 'gTTS'} | CapCut Sync: ${serverCapabilities.capcut_dir || 'ZIP 1-Click'}`;
            }
            if (hint) {
                hint.innerHTML = `✅ Đã kết nối <strong>Local Server</strong>: Nút bên dưới sẽ render trực tiếp kịch bản bạn đang chỉnh (<strong>Timeline 4 Tracks + Giọng 1.0x</strong>)${serverCapabilities.capcut_dir ? ' và tự đồng bộ vào CapCut Desktop!' : '!'}`;
            }
            return;
        }
    } catch (e) {
        serverAvailable = false;
    }

    if (badge) {
        badge.className = 'server-pill offline';
        badge.textContent = '🌐 Chế Độ Web Tĩnh';
    }
}

function _downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
        if (a.parentNode) document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 5000);
}

async function exportCapCutFromStudio(event) {
    if (currentStudioMode === 'fb') {
        if (event) event.preventDefault();
        showToast('ℹ️ Chế độ Bài FB là ảnh tĩnh — hãy bấm "📷 Chụp Ảnh (.PNG)" hoặc chuyển sang Chat 1-1 / Group!', 'warn', 4200);
        return;
    }

    if (!serverAvailable) {
        // Để thẻ <a href="assets/Cua_Thep_TikTok_Luxury.zip" download> tự tải file mẫu tĩnh
        showToast('🌐 Đang tải gói mẫu Cửa Thép. Mở studio qua CHAY_STUDIO.bat/.sh để xuất theo kịch bản tùy chỉnh!', 'info', 4500);
        return;
    }

    if (event) event.preventDefault();
    const sc = scenarios[currentScenarioKey];
    if (!sc || !sc.messages || sc.messages.length === 0) {
        showToast('⚠️ Kịch bản hiện tại đang rỗng!', 'warn');
        return;
    }

    const btn = document.getElementById('btn-download-capcut');
    const mp4Btn = document.getElementById('btn-export-mp4');
    const statusText = document.getElementById('render-status');
    const origHtml = btn ? btn.innerHTML : '';
    const slug = buildExportSlug(sc.title, currentScenarioKey);

    try {
        if (btn) {
            btn.classList.add('loading');
            btn.innerHTML = '⏳ Đang Render Frames & Voice...';
            btn.style.pointerEvents = 'none';
        }
        if (mp4Btn) mp4Btn.disabled = true;
        if (statusText) {
            statusText.style.display = 'block';
            statusText.innerHTML = '📦 Đang đóng gói dự án CapCut 4 Tracks (Chromium Retina + Giọng 1.0x)...';
        }

        const resp = await fetch('/api/export-capcut', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario: sc,
                characters: characterRoster,
                projectName: slug,
                syncToCapCut: true
            })
        });

        if (!resp.ok) {
            const errJson = await resp.json().catch(() => ({}));
            throw new Error(errJson.error || `HTTP ${resp.status}`);
        }

        const blob = await resp.blob();
        const synced = resp.headers.get('X-CapCut-Synced') === '1';
        const dur = resp.headers.get('X-CapCut-Duration') || '?';
        _downloadBlob(blob, `${slug}.zip`);

        if (statusText) {
            statusText.innerHTML = synced
                ? `✅ Đã tạo ${slug}.zip (${dur}s) & tự đồng bộ thẳng vào CapCut Desktop!`
                : `✅ Đã tạo & tải về ${slug}.zip (${dur}s) — Giải nén và chạy CAI_DAT_VAO_CAPCUT!`;
        }
        showToast(
            synced ? `🚀 Đã xuất ${slug}.zip & đồng bộ vào CapCut!` : `✅ Đã tải xuống ${slug}.zip (${dur}s)!`,
            'success',
            4800
        );
    } catch (err) {
        console.error('[Export CapCut]', err);
        if (statusText) statusText.style.display = 'none';
        showToast('⚠️ Lỗi xuất CapCut: ' + err.message, 'error', 5000);
    } finally {
        if (btn) {
            btn.classList.remove('loading');
            btn.innerHTML = origHtml;
            btn.style.pointerEvents = 'auto';
        }
        if (mp4Btn) mp4Btn.disabled = false;
    }
}

async function exportMp4FromStudio() {
    if (currentStudioMode === 'fb') {
        showToast('ℹ️ Chế độ Bài FB là ảnh tĩnh — hãy dùng nút "📷 Chụp Ảnh (.PNG)" bên dưới!', 'warn', 4000);
        return;
    }

    if (!serverAvailable) {
        showToast('ℹ️ Chế độ Web Tĩnh: Chạy CHAY_STUDIO.bat/.sh để xuất MP4 1080×1920, hoặc bấm "⏺ Ghi Hình Web (.WEBM)".', 'warn', 5000);
        return;
    }

    const sc = scenarios[currentScenarioKey];
    if (!sc || !sc.messages || sc.messages.length === 0) {
        showToast('⚠️ Kịch bản hiện tại đang rỗng!', 'warn');
        return;
    }

    const btn = document.getElementById('btn-export-mp4');
    const capBtn = document.getElementById('btn-download-capcut');
    const statusText = document.getElementById('render-status');
    const origHtml = btn ? btn.innerHTML : '';
    const slug = buildExportSlug(sc.title, 'TikTok_Video');

    try {
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '⏳ Đang Render Video MP4 (H.264/AAC)...';
        }
        if (capBtn) capBtn.style.pointerEvents = 'none';
        if (statusText) {
            statusText.style.display = 'block';
            statusText.innerHTML = '🎬 Đang dựng Video 1080×1920 (Chromium Frames + Voice 1.0x + FFmpeg)...';
        }

        const resp = await fetch('/api/export-mp4', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario: sc,
                characters: characterRoster,
                projectName: slug
            })
        });

        if (!resp.ok) {
            const errJson = await resp.json().catch(() => ({}));
            throw new Error(errJson.error || `HTTP ${resp.status}`);
        }

        const blob = await resp.blob();
        const dur = resp.headers.get('X-CapCut-Duration') || '?';
        _downloadBlob(blob, `${slug}.mp4`);

        if (statusText) {
            statusText.innerHTML = `✅ Đã xuất hoàn chỉnh ${slug}.mp4 (${dur}s, 1080×1920)!`;
        }
        showToast(`🎬 Xuất MP4 thành công (${dur}s)!`, 'success', 4800);
    } catch (err) {
        console.error('[Export MP4]', err);
        if (statusText) statusText.style.display = 'none';
        showToast('⚠️ Lỗi render MP4: ' + err.message, 'error', 5000);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
        if (capBtn) capBtn.style.pointerEvents = 'auto';
    }
}


// ============================================================================
// 7. LOGIC GROUP CHAT, FACEBOOK POST MODE & TOGGLE HIỂN THỊ
// ============================================================================
let currentStudioMode = 'chat'; // 'chat', 'group', or 'fb'
let groupChatSettings = {
    name: 'Văn Phòng Cửa Thép Luxury',
    unread: 8,
    avatar: 'assets/steel_door_logo.png',
    wallpaper: 'assets/bg_anime_sky.jpg',
    bubbleColor: '#e0f2fe'
};

function toggleBottomBarVisibility(show) {
    document.body.classList.toggle('hide-bottom-bar', !show);
    const cb = document.getElementById('toggle-bottom-bar');
    if (cb) cb.checked = !!show;
    if (_dbReady && typeof saveSetting === 'function') {
        saveSetting('pref_show_bottom_bar', !!show).catch(() => {});
    }
}

function toggleChatAnimations(enabled) {
    document.body.classList.toggle('no-chat-anim', !enabled);
    const cb = document.getElementById('toggle-animations');
    if (cb) cb.checked = !!enabled;
    if (_dbReady && typeof saveSetting === 'function') {
        saveSetting('pref_enable_animations', !!enabled).catch(() => {});
    }
}

function syncModeButtonsAndPanels(mode) {
    const btnChat = document.getElementById('btn-mode-chat');
    const btnGroup = document.getElementById('btn-mode-group');
    const btnFb = document.getElementById('btn-mode-fb');

    if (btnChat) btnChat.className = mode === 'chat' ? 'btn-primary' : 'btn-secondary';
    if (btnGroup) btnGroup.className = mode === 'group' ? 'btn-primary' : 'btn-secondary';
    if (btnFb) btnFb.className = mode === 'fb' ? 'btn-primary' : 'btn-secondary';

    const panelChat = document.getElementById('panel-chat-mode');
    const panelGroup = document.getElementById('panel-group-mode');
    const panelFb = document.getElementById('panel-fb-mode');

    if (panelChat) panelChat.style.display = (mode === 'chat' || mode === 'group') ? 'block' : 'none';
    if (panelGroup) panelGroup.style.display = mode === 'group' ? 'flex' : 'none';
    if (panelFb) panelFb.style.display = mode === 'fb' ? 'flex' : 'none';

    const frameChat = document.getElementById('frame-chat-mode');
    const frameGroup = document.getElementById('frame-group-mode');
    const frameFb = document.getElementById('frame-fb-mode');

    if (frameChat) frameChat.style.display = mode === 'chat' ? 'flex' : 'none';
    if (frameGroup) frameGroup.style.display = mode === 'group' ? 'flex' : 'none';
    if (frameFb) frameFb.style.display = mode === 'fb' ? 'flex' : 'none';

    const playGroup = document.querySelector('.control-group');
    if (playGroup) {
        playGroup.style.display = (mode === 'chat' || mode === 'group') ? 'flex' : 'none';
    }
}

function switchStudioMode(mode) {
    currentStudioMode = mode;
    syncModeButtonsAndPanels(mode);

    if (mode === 'group') {
        const curSc = scenarios[currentScenarioKey];
        const targetKey = (curSc && curSc.theme === 'group_messenger')
            ? currentScenarioKey
            : (scenarios['scenario_group_cuathep']
                ? 'scenario_group_cuathep'
                : (Object.keys(scenarios).find(k => scenarios[k]?.theme === 'group_messenger') || Object.keys(scenarios)[0]));
        if (targetKey) {
            selectScenario(targetKey);
        } else {
            renderGroupHeader();
            resetChat();
            renderAllMessagesInstant();
        }
    } else if (mode === 'chat') {
        const curSc = scenarios[currentScenarioKey];
        const targetKey = (curSc && curSc.theme !== 'group_messenger')
            ? currentScenarioKey
            : (scenarios['scenario_1']
                ? 'scenario_1'
                : (Object.keys(scenarios).find(k => scenarios[k]?.theme !== 'group_messenger') || Object.keys(scenarios)[0]));
        if (targetKey) {
            selectScenario(targetKey);
        } else {
            renderPhoneHeader();
            resetChat();
            renderAllMessagesInstant();
        }
    } else if (mode === 'fb') {
        stopAllPlayback();
        renderFbPost();
    }
}

function renderGroupHeader() {
    const nameEl = document.getElementById('group-render-name');
    const unreadEl = document.getElementById('group-unread-badge');
    const avatarEl = document.getElementById('group-render-avatar');

    const sc = scenarios[currentScenarioKey];
    const name = sc?.groupName || groupChatSettings.name;
    const unread = sc?.groupUnread !== undefined ? sc.groupUnread : groupChatSettings.unread;
    const avatar = sc?.groupAvatar || groupChatSettings.avatar;

    if (nameEl) nameEl.textContent = name;
    if (unreadEl) unreadEl.textContent = unread;
    if (avatarEl) avatarEl.src = avatar;

    const nameInput = document.getElementById('group-name-input');
    const unreadInput = document.getElementById('group-unread-input');
    if (nameInput) nameInput.value = name;
    if (unreadInput) unreadInput.value = unread;

    const bgUrl = sc?.bgWallpaper || groupChatSettings.wallpaper;
    const groupWin = document.getElementById('group-chat-window');
    if (groupWin) {
        groupWin.style.backgroundImage = `url('${bgUrl}')`;
        const bColor = sc?.bubbleColor || groupChatSettings.bubbleColor;
        groupWin.style.setProperty('--group-bubble-color', bColor);
    }

    // Đồng bộ active preset card/pill
    document.querySelectorAll('.bg-preset-card').forEach(c => c.classList.remove('active'));
    if (bgUrl === 'assets/bg_anime_sky.jpg') document.getElementById('bg-card-sky')?.classList.add('active');
    else if (bgUrl === 'assets/bg_anime_sunset.jpg') document.getElementById('bg-card-sunset')?.classList.add('active');

    const bColor = sc?.bubbleColor || groupChatSettings.bubbleColor;
    document.querySelectorAll('.bubble-color-pill').forEach(p => p.classList.remove('active'));
    const colorMap = { '#e0f2fe': 'pill-blue', '#ffd8e8': 'pill-pink', '#d1fae5': 'pill-mint', '#ffffff': 'pill-white' };
    if (colorMap[bColor]) document.getElementById(colorMap[bColor])?.classList.add('active');
}

function updateGroupHeaderFromInputs() {
    const nameInput = document.getElementById('group-name-input');
    const unreadInput = document.getElementById('group-unread-input');
    if (nameInput) {
        const val = nameInput.value.trim() || 'Văn Phòng Cửa Thép Luxury';
        groupChatSettings.name = val;
        if (scenarios[currentScenarioKey]) scenarios[currentScenarioKey].groupName = val;
        const nameEl = document.getElementById('group-render-name');
        if (nameEl) nameEl.textContent = val;
    }
    if (unreadInput) {
        const val = parseInt(unreadInput.value, 10) || 0;
        groupChatSettings.unread = val;
        if (scenarios[currentScenarioKey]) scenarios[currentScenarioKey].groupUnread = val;
        const unreadEl = document.getElementById('group-unread-badge');
        if (unreadEl) unreadEl.textContent = val;
    }
    scheduleSaveScenarios();
}

function setGroupWallpaper(url, key) {
    groupChatSettings.wallpaper = url;
    if (scenarios[currentScenarioKey]) scenarios[currentScenarioKey].bgWallpaper = url;
    const groupWin = document.getElementById('group-chat-window');
    if (groupWin) {
        groupWin.style.backgroundImage = `url('${url}')`;
    }

    document.querySelectorAll('.bg-preset-card').forEach(c => c.classList.remove('active'));
    const activeCard = document.getElementById(`bg-card-${key}`);
    if (activeCard) activeCard.classList.add('active');
    saveScenariosToStorage();
}

function handleGroupBgUpload(input) {
    const file = input?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function (e) {
        const img = new Image();
        img.onload = function () {
            const maxH = 1280;
            let w = img.width;
            let h = img.height;
            if (h > maxH) {
                w = Math.round((w * maxH) / h);
                h = maxH;
            }
            const canvas = document.createElement('canvas');
            canvas.width = w;
            canvas.height = h;
            canvas.getContext('2d').drawImage(img, 0, 0, w, h);
            setGroupWallpaper(canvas.toDataURL('image/jpeg', 0.88), 'custom');
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function setGroupBubbleColor(color, key) {
    groupChatSettings.bubbleColor = color;
    if (scenarios[currentScenarioKey]) scenarios[currentScenarioKey].bubbleColor = color;
    const groupWin = document.getElementById('group-chat-window');
    if (groupWin) {
        groupWin.style.setProperty('--group-bubble-color', color);
    }

    document.querySelectorAll('.bubble-color-pill').forEach(p => p.classList.remove('active'));
    const activePill = document.getElementById(`pill-${key}`);
    if (activePill) activePill.classList.add('active');
    saveScenariosToStorage();
}

function handleGroupAvatarUpload(input) {
    const file = input?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function (e) {
        const img = new Image();
        img.onload = function () {
            const maxDim = 256;
            let w = img.width;
            let h = img.height;
            if (w > maxDim || h > maxDim) {
                if (w > h) { h = Math.round((h * maxDim) / w); w = maxDim; }
                else { w = Math.round((w * maxDim) / h); h = maxDim; }
            }
            const canvas = document.createElement('canvas');
            canvas.width = w;
            canvas.height = h;
            canvas.getContext('2d').drawImage(img, 0, 0, w, h);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.88);

            groupChatSettings.avatar = dataUrl;
            if (scenarios[currentScenarioKey]) scenarios[currentScenarioKey].groupAvatar = dataUrl;
            const avatarEl = document.getElementById('group-render-avatar');
            if (avatarEl) avatarEl.src = dataUrl;
            saveScenariosToStorage();
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function loadCuaThepScenario() {
    let key = 'scenario_group_cuathep';
    if (!scenarios[key]) {
        scenarios[key] = JSON.parse(JSON.stringify(DEFAULT_SCENARIOS.scenario_group_cuathep));
        saveScenariosToStorage();
    }
    switchStudioMode('group');
    selectScenario(key);
    switchTab('builder');
}

function loadPetBiteScenario() {
    loadCuaThepScenario();
}

function changeGroupLineSender(index, charId) {
    const data = scenarios[currentScenarioKey];
    if (!data || !data.messages[index]) return;
    const char = characterRoster.find(c => c.id === charId);
    if (char) {
        data.messages[index].senderId = char.id;
        data.messages[index].senderName = char.name;
        data.messages[index].sender = char.role || 'customer';
        data.messages[index].sfx = char.role === 'owner' ? 'pop' : 'ting';
    }
    saveScenariosToStorage();
    renderScriptBuilder();
    resetChat();
    renderAllMessagesInstant();
}

function renderFbPost() {
    const author = document.getElementById('fb-author-name')?.value || '';
    const content = document.getElementById('fb-post-content')?.value || '';
    const likes = document.getElementById('fb-likes')?.value || '';
    const comments = document.getElementById('fb-comments')?.value || '';

    const nameEl = document.getElementById('fb-render-name');
    const contentEl = document.getElementById('fb-render-content');
    const likesEl = document.getElementById('fb-render-likes');
    const commentsEl = document.getElementById('fb-render-comments');

    if (nameEl) nameEl.textContent = author || 'Người dùng ẩn danh';
    if (contentEl) contentEl.textContent = content;
    if (likesEl) likesEl.textContent = likes;
    if (commentsEl) commentsEl.textContent = comments;
}

function handleFbAvatarUpload(input) {
    const file = input?.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function (e) {
        const el = document.getElementById('fb-render-avatar');
        if (el) el.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function handleFbImageUpload(input) {
    const file = input?.files?.[0];
    const container = document.getElementById('fb-render-image-container');
    const img = document.getElementById('fb-render-image');
    if (!container || !img) return;

    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            img.src = e.target.result;
            container.style.display = 'flex';
        };
        reader.readAsDataURL(file);
    } else {
        container.style.display = 'none';
        img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
    }
}


// ============================================================================
// 8. ĐIỀU HƯỚNG MOBILE, ĐỒNG HỒ & KHỞI TẠO HỆ THỐNG
// ============================================================================
function updateClock() {
    const clockEl = document.getElementById('phone-time');
    if (!clockEl) return;
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    clockEl.textContent = `${h}:${m}`;
}

function switchMobileTab(tab) {
    document.querySelectorAll('.mobile-nav-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById(`mob-tab-${tab}`);
    if (activeBtn) activeBtn.classList.add('active');

    const leftPanel = document.querySelector('.side-panel:not(.right-panel)');
    const stage = document.querySelector('.preview-stage');
    const rightPanel = document.querySelector('.right-panel');

    if (window.innerWidth <= 900) {
        if (leftPanel) leftPanel.style.display = (tab === 'left') ? 'block' : 'none';
        if (stage) stage.style.display = (tab === 'preview') ? 'flex' : 'none';
        if (rightPanel) rightPanel.style.display = (tab === 'right') ? 'block' : 'none';
    }
}

window.addEventListener('resize', () => {
    const leftPanel = document.querySelector('.side-panel:not(.right-panel)');
    const stage = document.querySelector('.preview-stage');
    const rightPanel = document.querySelector('.right-panel');
    if (window.innerWidth > 900) {
        // Giữ Cột Trái luôn hiển thị trên Desktop ngay cả ở FB Mode (vì form soạn bài FB nằm trong Cột Trái)
        if (leftPanel) leftPanel.style.display = 'block';
        if (stage) stage.style.display = 'flex';
        if (rightPanel) rightPanel.style.display = 'block';
    } else {
        const activeMob = document.querySelector('.mobile-nav-btn.active');
        if (activeMob) {
            const tab = activeMob.id.replace('mob-tab-', '');
            switchMobileTab(tab);
        }
    }
});

function copyCapCutPath(pathStr, btnId) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(pathStr).then(() => {
            showCopyFeedback(btnId);
        }).catch(() => {
            fallbackCopy(pathStr, btnId);
        });
    } else {
        fallbackCopy(pathStr, btnId);
    }
}

function fallbackCopy(text, btnId) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
        document.execCommand('copy');
        showCopyFeedback(btnId);
    } catch (e) {
        showToast('Đường dẫn: ' + text, 'info', 4000);
    }
    document.body.removeChild(ta);
}

function showCopyFeedback(btnId) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    const oldHtml = btn.innerHTML;
    btn.innerHTML = '✅ Đã chép!';
    btn.style.borderColor = '#10b981';
    btn.style.color = '#10b981';
    setTimeout(() => {
        btn.innerHTML = oldHtml;
        btn.style.borderColor = '';
        btn.style.color = '';
    }, 2000);
}

window.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const isHeadlessRender = urlParams.get('render') === '1';

    if (isHeadlessRender) {
        document.body.classList.add('no-chat-anim');
    }

    // ---- 1. Khởi tạo IndexedDB & khôi phục dữ liệu ----
    try {
        if (typeof migrateFromLocalStorage === 'function') {
            const existingChars = await migrateFromLocalStorage();
            if (existingChars && existingChars.length > 0) {
                characterRoster = existingChars.map(normalizeCharacterItem);
                const schemaMigrated = await loadSetting('studio_chars_schema_v2');
                if (!schemaMigrated) {
                    defaultCharacters.forEach(def => {
                        if (!characterRoster.some(c => c.id === def.id)) {
                            characterRoster.push({ ...def });
                        }
                    });
                    await saveCharactersToIndexedDB(characterRoster);
                    await saveSetting('studio_chars_schema_v2', true);
                }
            } else {
                characterRoster = defaultCharacters.map(c => ({ ...c }));
                await saveCharactersToIndexedDB(characterRoster);
                await saveSetting('studio_chars_schema_v2', true);
            }

            // Nạp kịch bản đã lưu từ IndexedDB nếu có
            const savedScenarios = await loadScenariosFromIndexedDB();
            if (savedScenarios && Object.keys(savedScenarios).length > 0) {
                scenarios = attachLegacyScenarioAliases(savedScenarios);
            } else {
                await saveAllScenariosToIndexedDB(scenarios);
            }

            // Nạp API key & tùy chọn hiển thị
            const savedKey = await loadSetting('gemini_api_key');
            const keyInput = document.getElementById('ai-api-key');
            if (savedKey && keyInput) keyInput.value = savedKey;

            if (!isHeadlessRender) {
                const showBottomBar = await loadSetting('pref_show_bottom_bar');
                if (showBottomBar !== null) {
                    document.body.classList.toggle('hide-bottom-bar', !showBottomBar);
                    const cbBar = document.getElementById('toggle-bottom-bar');
                    if (cbBar) cbBar.checked = !!showBottomBar;
                }
                const enableAnim = await loadSetting('pref_enable_animations');
                if (enableAnim !== null) {
                    document.body.classList.toggle('no-chat-anim', !enableAnim);
                    const cbAnim = document.getElementById('toggle-animations');
                    if (cbAnim) cbAnim.checked = !!enableAnim;
                }
            }
        }
        _dbReady = true;
    } catch (e) {
        console.warn('IndexedDB init failed, using defaults:', e);
        characterRoster = defaultCharacters.map(c => ({ ...c }));
    }

    // ---- 2. Render danh sách nhân vật & kịch bản ----
    renderCharacterRoster();
    renderScenarioCards();
    updateVoiceUploadStatusUI();

    // ---- 3. Kích hoạt Mode & Kịch bản khởi đầu ----
    const scenarioParam = urlParams.get('scenario');
    const modeParam = urlParams.get('mode');
    if (scenarioParam && scenarios[scenarioParam]) {
        selectScenario(scenarioParam);
    } else if (modeParam === 'group') {
        switchStudioMode('group');
    } else if (modeParam === 'fb') {
        switchStudioMode('fb');
    } else {
        selectScenario(scenarios['scenario_1'] ? 'scenario_1' : Object.keys(scenarios)[0]);
    }

    updateClock();
    setInterval(updateClock, 15000);

    // ---- 4. Event Listeners ----
    const avatarInput = document.getElementById('char-input-avatar-file');
    if (avatarInput) {
        avatarInput.addEventListener('change', (e) => handleAvatarFileSelect(e.target));
    }
    const voiceInputFile = document.getElementById('char-input-voice-file');
    if (voiceInputFile) {
        voiceInputFile.addEventListener('change', (e) => handleVoiceFileSelect(e.target));
    }
    const voiceSelect = document.getElementById('char-input-voice');
    if (voiceSelect) {
        voiceSelect.addEventListener('change', () => updateVoiceUploadStatusUI());
    }

    // ---- 5. Kiểm tra Local Backend Server ----
    if (!isHeadlessRender) {
        checkServerHealth();
    }
});
