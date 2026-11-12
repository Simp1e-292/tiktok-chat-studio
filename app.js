// ============================================================================
// 1. QUẢN LÝ NHÂN VẬT & NÉN ẢNH AVATAR SIÊU NHẸ (CHARACTER ROSTER & RESIZE)
// ============================================================================
const defaultCharacters = [
    {
        id: "char_sep",
        name: "SẾP TỔNG",
        avatar: "assets/avatar_sep.png",
        role: "owner",
        pitch: 0.95
    },
    {
        id: "char_hai",
        name: "Hải Kỹ Thuật",
        avatar: "assets/avatar_hai.png",
        role: "customer",
        pitch: 1.05
    },
    {
        id: "char_vy",
        name: "Vy Kế Toán",
        avatar: "assets/avatar_vy.png",
        role: "customer",
        pitch: 1.25
    },
    {
        id: "char_thang",
        name: "Thắng Công Trình",
        avatar: "assets/avatar_thang.png",
        role: "customer",
        pitch: 1.1
    },
    {
        id: "char_cuathep_vip",
        name: "Cửa Thép Luxury",
        avatar: "assets/steel_door_logo.png",
        role: "owner",
        pitch: 0.95
    }
];

let characterRoster = [...defaultCharacters];

let uploadedAvatarBase64 = "assets/customer_avatar.png";
let editingCharIndex = null; // null = chế độ Thêm Mới, số = vị trí nhân vật đang Sửa
let _dbReady = false; // Flag: IndexedDB đã sẵn sàng chưa

// Lưu nhân vật vào IndexedDB (thay thế localStorage)
function saveCharactersToStorage() {
    if (_dbReady) {
        // Async save — không block UI
        saveCharactersToIndexedDB(characterRoster).catch(e => {
            console.error('IndexedDB save error:', e);
        });
    }
    // Fallback: vẫn lưu localStorage cho an toàn
    try {
        localStorage.setItem('tiktok_studio_characters_v2', JSON.stringify(characterRoster));
    } catch (e) {
        // Bỏ qua nếu localStorage đầy — IndexedDB đã xử lý
        console.warn('localStorage save failed (OK — IndexedDB is primary):', e.message);
    }
}

// Hiển thị danh sách nhân vật
function renderCharacterRoster() {
    const container = document.getElementById('character-list-container');
    if (!container) return;
    container.innerHTML = '';

    characterRoster.forEach((char, idx) => {
        const isOwner = char.role === 'owner';
        const isBeingEdited = (editingCharIndex === idx);
        const card = document.createElement('div');
        card.className = `character-card ${isBeingEdited ? 'editing' : ''}`;
        card.innerHTML = `
            <div class="character-info">
                <div class="char-avatar-box">
                    <img src="${char.avatar}" alt="Avatar" onerror="this.src='assets/customer_avatar.png'">
                </div>
                <div class="char-details">
                    <h4>${char.name}</h4>
                    <span class="char-badge ${isOwner ? 'owner' : 'customer'}">
                        ${isOwner ? '👑 Chủ Tiệm / Shop (Bên phải)' : '💬 Khách Hàng (Bên trái)'}
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

// Chỉnh sửa một nhân vật (Đưa dữ liệu ngược lên form)
function editCharacter(idx) {
    const char = characterRoster[idx];
    if (!char) return;

    editingCharIndex = idx;

    const formCard = document.getElementById('char-form-card');
    const formTitle = document.getElementById('char-form-title');
    const nameInput = document.getElementById('char-input-name');
    const roleInput = document.getElementById('char-input-role');
    const pitchInput = document.getElementById('char-input-pitch');
    const btnSubmit = document.getElementById('btn-save-char');
    const btnCancel = document.getElementById('btn-cancel-edit-char');
    const previewEl = document.getElementById('avatar-preview-img');

    if (formCard) formCard.classList.add('edit-mode');
    if (formTitle) formTitle.innerHTML = `✏️ Đang Chỉnh Sửa: <strong>${char.name}</strong>`;
    if (nameInput) nameInput.value = char.name;
    if (roleInput) roleInput.value = char.role;
    if (pitchInput) {
        pitchInput.value = char.pitch ? String(char.pitch) : "1.1";
    }
    
    uploadedAvatarBase64 = char.avatar || "assets/customer_avatar.png";
    if (previewEl) previewEl.src = uploadedAvatarBase64;

    if (btnSubmit) btnSubmit.innerHTML = "💾 Cập Nhật Nhân Vật Này";
    if (btnCancel) btnCancel.style.display = "inline-flex";

    renderCharacterRoster();

    if (formCard) {
        formCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Hủy chế độ chỉnh sửa, trả form về Tạo Mới
function cancelEditCharacter() {
    editingCharIndex = null;

    const formCard = document.getElementById('char-form-card');
    const formTitle = document.getElementById('char-form-title');
    const nameInput = document.getElementById('char-input-name');
    const btnSubmit = document.getElementById('btn-save-char');
    const btnCancel = document.getElementById('btn-cancel-edit-char');
    const previewEl = document.getElementById('avatar-preview-img');
    const fileInput = document.getElementById('char-input-avatar-file');

    if (formCard) formCard.classList.remove('edit-mode');
    if (formTitle) formTitle.innerHTML = "➕ Thêm Nhân Vật Mới Vao Studio";
    if (nameInput) nameInput.value = "";
    if (fileInput) fileInput.value = "";

    uploadedAvatarBase64 = "assets/customer_avatar.png";
    if (previewEl) previewEl.src = "assets/customer_avatar.png";

    if (btnSubmit) btnSubmit.innerHTML = "💾 Lưu & Thêm Vào Dàn Nhân Vật";
    if (btnCancel) btnCancel.style.display = "none";

    renderCharacterRoster();
}

// Tự động Nén & Thu nhỏ ảnh xuống dưới ~10KB (Max Width/Height 200px)
function handleAvatarFileSelect(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = new Image();
            img.onload = function() {
                // Resize qua Canvas để không bao giờ bị lỗi Quota Exceeded của localStorage
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

                // Chuyển sang DataURL nén JPEG chất lượng 0.85
                uploadedAvatarBase64 = canvas.toDataURL('image/jpeg', 0.85);
                const previewEl = document.getElementById('avatar-preview-img');
                if (previewEl) previewEl.src = uploadedAvatarBase64;
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
}

// Thêm Mới hoặc Cập Nhật nhân vật (Đã xử lý lỗi và phản hồi tức thì)
function saveOrUpdateCharacter() {
    const nameInput = document.getElementById('char-input-name');
    const roleInput = document.getElementById('char-input-role');
    const pitchInput = document.getElementById('char-input-pitch');

    if (!nameInput || !nameInput.value.trim()) {
        alert('⚠️ Vui lòng nhập tên cho nhân vật / shop của bạn!');
        if (nameInput) nameInput.focus();
        return;
    }

    const nameVal = nameInput.value.trim();
    const roleVal = roleInput ? roleInput.value : 'customer';
    const pitchVal = pitchInput ? (parseFloat(pitchInput.value) || 1.0) : 1.0;

    if (editingCharIndex !== null && characterRoster[editingCharIndex]) {
        // ĐANG Ở CHẾ ĐỘ SỬA
        const updatedChar = characterRoster[editingCharIndex];
        updatedChar.name = nameVal;
        updatedChar.role = roleVal;
        updatedChar.pitch = pitchVal;
        updatedChar.avatar = uploadedAvatarBase64;

        try {
            saveCharactersToStorage();
        } catch (e) {
            alert('⚠️ Lỗi lưu vào bộ nhớ trình duyệt: ' + e.message);
            return;
        }

        const msg = `🎉 Đã CẬP NHẬT thành công: "${updatedChar.name}"! Màn hình video đã tự động đổi tên và avatar mới.`;
        
        cancelEditCharacter();
        renderPhoneHeader();
        renderScriptBuilder();
        alert(msg);
    } else {
        // ĐANG Ở CHẾ ĐỘ TẠO MỚI
        const newChar = {
            id: 'char_' + Date.now(),
            name: nameVal,
            avatar: uploadedAvatarBase64,
            role: roleVal,
            pitch: pitchVal
        };

        characterRoster.push(newChar);
        
        try {
            saveCharactersToStorage();
        } catch (e) {
            characterRoster.pop();
            alert('⚠️ Lỗi bộ nhớ trình duyệt đầy! Vui lòng dùng ảnh kích thước nhỏ hơn hoặc hệ thống sẽ tự nén.');
            return;
        }

        cancelEditCharacter();
        renderPhoneHeader();
        renderScriptBuilder();
        alert(`🎉 Đã THÊM MỚI thành công nhân vật "${newChar.name}"!`);
    }
}

function deleteCharacter(idx) {
    if (characterRoster.length <= 1) {
        alert("⚠️ Hệ thống cần giữ lại ít nhất 01 nhân vật để duy trì khung hội thoại!");
        return;
    }

    const target = characterRoster[idx];
    if (confirm(`Bạn có chắc muốn xóa nhân vật "${target.name}" khỏi hệ thống không?`)) {
        if (editingCharIndex === idx) {
            cancelEditCharacter();
        } else if (editingCharIndex !== null && editingCharIndex > idx) {
            editingCharIndex--;
        }

        characterRoster.splice(idx, 1);
        saveCharactersToStorage();
        renderCharacterRoster();
        renderPhoneHeader();
        resetChat();
        alert(`🗑️ Đã xóa nhân vật "${target.name}".`);
    }
}


// ============================================================================
// 2. DỮ LIỆU KỊCH BẢN & SOẠN THẢO TRỰC QUAN (SCRIPT BUILDER ENGINE)
// ============================================================================
let scenarios = {
    scenario_group_cuathep: {
        title: "🏢 [HÀI HƯỚC CỬA THÉP] Test Xe Nâng Húc Cửa & Pha Quay Xe Của Kế Toán",
        desc: "Drama hài hước văn phòng Cửa Thép: Hải KT test cửa chịu lực 10 tấn, xe nâng gãy càng cửa không xước, kế toán đòi trừ 5 triệu, Sếp chốt bao lẩu dê.",
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
                type: "text",
                content: "Hải Kỹ Thuật! Camera xưởng báo động đỏ! Cậu vừa lái xe nâng húc thẳng vào cửa chính công ty đấy à?!",
                delay: 1700,
                sfx: "pop"
            },
            {
                id: "gmsg_2",
                senderId: "char_hai",
                senderName: "Hải Kỹ Thuật",
                type: "text",
                content: "Oan cho em quá Sếp ơi! Em đang test độ bền cửa thép chịu lực 10 tấn cho khách xem thôi mà! 😅",
                delay: 1600,
                sfx: "ting"
            },
            {
                id: "gmsg_3",
                senderId: "char_vy",
                senderName: "Vy Kế Toán",
                type: "text",
                content: "Báo cáo Sếp: Xe nâng gãy đôi càng rồi ạ, còn cánh cửa thép thì đến một vết xước cũng không có! 😂",
                delay: 1500,
                sfx: "ting"
            },
            {
                id: "gmsg_4",
                senderId: "char_thang",
                senderName: "Thắng Công Trình",
                type: "text",
                content: "Em vừa lấy búa tạ 10 cân phang thử, búa nảy ngược lại suýt đập trúng trán em đây này Sếp! 🔨",
                delay: 1500,
                sfx: "ting"
            },
            {
                id: "gmsg_5",
                senderId: "char_hai",
                senderName: "Hải Kỹ Thuật",
                type: "text",
                content: "Cửa thép nhà mình thế này trộm vào chỉ có nước ngồi khóc xin ngụm nước rồi đi về thôi Sếp ạ! 🤣",
                delay: 1500,
                sfx: "ting"
            },
            {
                id: "gmsg_6",
                senderId: "char_vy",
                senderName: "Vy Kế Toán",
                type: "text",
                content: "Cửa đỉnh thật nhưng tiền sửa xe nâng 5 triệu thì trừ vào lương anh Hải hay lương Sếp đây ạ? 📝",
                delay: 1500,
                sfx: "ting"
            },
            {
                id: "gmsg_7",
                senderId: "char_hai",
                senderName: "Hải Kỹ Thuật",
                type: "text",
                content: "Ủa em Vy?! Người cùng một nhà sao em quay xe khét lẹt vậy em?! Cứu em Sếp ơi! 😭",
                delay: 1400,
                sfx: "ting"
            },
            {
                id: "gmsg_8",
                senderId: "char_sep",
                senderName: "SẾP TỔNG",
                type: "text",
                content: "Trừ lương Hải! Nhưng tối nay Sếp bao cả xưởng nồi lẩu dê vì cửa quá đỉnh! Duyệt luôn! 👍",
                delay: 1200,
                sfx: "pop"
            }
        ]
    },
    get scenario_group_petbite() { return this.scenario_group_cuathep; },
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
                content: "Chất quá shop ơi! Cho em 2 hộp luôn nhé, đang rất cần để chiến nọ công việc! 🔥",
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

let currentScenarioKey = "scenario_1";
let isPlaying = false;
let audioCtx = null;
let synth = window.speechSynthesis;
let voices = [];

function getScenarioParticipants(scenarioData) {
    let owner = characterRoster.find(c => c.id === scenarioData.ownerCharId) || characterRoster.find(c => c.role === 'owner') || characterRoster[0] || defaultCharacters[0];
    let customer = characterRoster.find(c => c.id === scenarioData.customerCharId) || characterRoster.find(c => c.role === 'customer') || characterRoster[1] || defaultCharacters[1];
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
        selectOwner.value = currentData.ownerCharId || characterRoster[0].id;
        selectCust.value = currentData.customerCharId || characterRoster[1]?.id || characterRoster[0].id;
    }
}

function renderScriptBuilder() {
    const data = scenarios[currentScenarioKey];
    if (!data) return;

    const titleInput = document.getElementById('builder-scenario-title');
    if (titleInput) titleInput.value = data.title;

    updateBuilderParticipantDropdowns();

    const container = document.getElementById('builder-dialogue-list');
    if (!container) return;
    container.innerHTML = '';

    const { owner, customer } = getScenarioParticipants(data);

    data.messages.forEach((msg, index) => {
        const isCust = msg.sender === 'customer';
        const card = document.createElement('div');
        card.className = `dialogue-card ${isCust ? 'left-bubble' : 'right-bubble'}`;
        card.id = `line-card-${index}`;

        let senderSelectHtml = '';
        if (currentStudioMode === 'group') {
            const curSenderId = msg.senderId || (msg.sender === 'owner' ? owner.id : customer.id);
            senderSelectHtml = `<select class="dialogue-sender-select" onchange="changeGroupLineSender(${index}, this.value)">`;
            characterRoster.forEach(c => {
                const isSel = (c.id === curSenderId || c.name === msg.senderName);
                senderSelectHtml += `<option value="${c.id}" ${isSel ? 'selected' : ''}>👤 ${c.name}</option>`;
            });
            senderSelectHtml += `</select>`;
        } else {
            senderSelectHtml = `
                <select class="dialogue-sender-select" onchange="changeLineSender(${index}, this.value)">
                    <option value="customer" ${isCust ? 'selected' : ''}>💬 Khách: ${customer.name}</option>
                    <option value="owner" ${!isCust ? 'selected' : ''}>👑 Tiệm: ${owner.name}</option>
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
                <button type="button" class="type-btn ${msg.type === 'product_card' ? 'active' : ''}" onclick="changeLineType(${index}, 'product_card')">📦 Thẻ sản phẩm Shop</button>
                <button type="button" class="type-btn ${msg.type === 'like_sticker' ? 'active' : ''}" onclick="changeLineType(${index}, 'like_sticker')">👍 Sticker Like Bự</button>
            </div>
        `;

        if (msg.type === 'text') {
            html += `
                <textarea class="input-field" rows="2" style="font-size:13px;" placeholder="Nhập nội dung tin nhắn thoại..." oninput="updateLineContent(${index}, 'content', this.value)">${msg.content || ''}</textarea>
            `;
        } else if (msg.type === 'product_card') {
            html += `
                <div class="product-form-fields">
                    <input type="text" class="input-field" placeholder="Tên sản phẩm..." value="${msg.content || ''}" oninput="updateLineContent(${index}, 'content', this.value)">
                    <div style="display:flex;gap:6px;">
                        <input type="text" class="input-field" placeholder="Giá tiền (e.g. 99.000₫)" value="${msg.price || ''}" oninput="updateLineContent(${index}, 'price', this.value)">
                        <input type="text" class="input-field" placeholder="Huy hiệu SALE (e.g. -20% HOT)" value="${msg.discount || ''}" oninput="updateLineContent(${index}, 'discount', this.value)">
                    </div>
                </div>
            `;
        } else if (msg.type === 'like_sticker') {
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

function changeLineSender(index, sender) {
    scenarios[currentScenarioKey].messages[index].sender = sender;
    scenarios[currentScenarioKey].messages[index].sfx = sender === 'customer' ? 'ting' : 'pop';
    renderScriptBuilder();
}

function changeLineType(index, type) {
    const msg = scenarios[currentScenarioKey].messages[index];
    msg.type = type;
    if (type === 'like_sticker') {
        msg.content = "👍";
    } else if (type === 'product_card' && !msg.price) {
        msg.content = "Vitamin C Kháng Mỏi Siêu HOT";
        msg.price = "99.000₫";
        msg.discount = "-20% SALE";
        msg.image = "assets/vitamin_c.png";
        msg.cta = "🛍 Chốt ngay trên TikTok Shop";
        msg.sfx = "special";
    }
    renderScriptBuilder();
}

function updateLineContent(index, field, value) {
    scenarios[currentScenarioKey].messages[index][field] = value;
}

function deleteLine(index) {
    if (scenarios[currentScenarioKey].messages.length <= 1) {
        alert('⚠️ Kịch bản cần có ít nhất 1 câu tin nhắn!');
        return;
    }
    scenarios[currentScenarioKey].messages.splice(index, 1);
    renderScriptBuilder();
}

function moveLineUp(index) {
    if (index > 0) {
        const temp = scenarios[currentScenarioKey].messages[index];
        scenarios[currentScenarioKey].messages[index] = scenarios[currentScenarioKey].messages[index - 1];
        scenarios[currentScenarioKey].messages[index - 1] = temp;
        renderScriptBuilder();
    }
}

function moveLineDown(index) {
    if (index < scenarios[currentScenarioKey].messages.length - 1) {
        const temp = scenarios[currentScenarioKey].messages[index];
        scenarios[currentScenarioKey].messages[index] = scenarios[currentScenarioKey].messages[index + 1];
        scenarios[currentScenarioKey].messages[index + 1] = temp;
        renderScriptBuilder();
    }
}

function addNewLineToScript() {
    const data = scenarios[currentScenarioKey];
    const lastSender = data.messages.length > 0 ? data.messages[data.messages.length - 1].sender : 'owner';
    const nextSender = lastSender === 'customer' ? 'owner' : 'customer';

    data.messages.push({
        id: "msg_" + Date.now(),
        sender: nextSender,
        type: "text",
        content: nextSender === 'customer' ? "Shop ơi cho em đặt thêm 1 combo nữa nhé!" : "Dạ vâng chốt đơn ngay cho bạn ạ! 💚",
        delay: 1500,
        sfx: nextSender === 'customer' ? 'ting' : 'pop'
    });

    renderScriptBuilder();
    setTimeout(() => {
        const list = document.getElementById('builder-dialogue-list');
        if (list) list.scrollTop = list.scrollHeight;
    }, 100);
}

function createNewCustomScenario() {
    const newKey = 'scenario_custom_' + Date.now();
    const owner = characterRoster.find(c => c.role === 'owner') || characterRoster[0];
    const cust = characterRoster.find(c => c.role === 'customer') || characterRoster[1] || characterRoster[0];

    scenarios[newKey] = {
        title: "✨ Kịch bản mới sáng tạo của bạn",
        desc: "Kịch bản tùy biến cá nhân hóa với sự góp mặt của dàn nhân vật riêng.",
        theme: "messenger_ios",
        ownerCharId: owner.id,
        customerCharId: cust.id,
        messages: [
            {
                id: "msg_1",
                sender: "customer",
                type: "text",
                content: "Chào Shop! Cho hỏi bên mình có món gì mát tim gan không ạ? 😄",
                delay: 1400,
                sfx: "ting"
            },
            {
                id: "msg_2",
                sender: "owner",
                type: "text",
                content: "Dạ có ngay! Mời bạn ngắm nghía Bảo Bối siêu hót bên mình nhé... ⚡",
                delay: 1600,
                sfx: "pop"
            }
        ]
    };

    selectScenario(newKey);
    switchTab('builder');
    alert("🎉 Đã tạo một Kịch Bản Mới! Hiện bạn đang ở trong Trình Soạn Thao Tác & Lời Thoại. Hãy tự do chỉnh sửa nhé!");
}

function applyScriptBuilderToStage() {
    const titleInput = document.getElementById('builder-scenario-title');
    const selectOwner = document.getElementById('select-builder-owner');
    const selectCust = document.getElementById('select-builder-customer');

    if (titleInput && titleInput.value.trim()) {
        scenarios[currentScenarioKey].title = titleInput.value.trim();
    }
    if (selectOwner && selectOwner.value) {
        scenarios[currentScenarioKey].ownerCharId = selectOwner.value;
    }
    if (selectCust && selectCust.value) {
        scenarios[currentScenarioKey].customerCharId = selectCust.value;
    }

    renderPhoneHeader();
    resetChat();
    renderAllMessagesInstant();
    alert("✨ [Đã Khớp Lệnh] Toàn bộ đoạn chat đã hiện lên màn hình! Bạn có thể bấm 'Chụp Ảnh Giao Diện' ngay.");
}

function renderAllMessagesInstant() {
    const data = scenarios[currentScenarioKey];
    if (!data || !data.messages) return;
    
    data.messages.forEach(msg => {
        appendMessage(msg);
    });
    
    const chatWindow = document.getElementById('chat-window');
    if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ============================================================================
// 3. TẦNG XỬ LÝ ÂM THANH & CHUYỂN TAB UI STUDIO
// ============================================================================
function initAudio() {
    if (!audioCtx && window.AudioContext) {
        audioCtx = new AudioContext();
    }
    if (synth && voices.length === 0) {
        voices = synth.getVoices();
    }
}

if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = () => {
        voices = window.speechSynthesis.getVoices();
    };
}

function playSFX(type) {
    const sfxEnabled = document.getElementById('toggle-sfx')?.checked;
    if (!sfxEnabled || !audioCtx) return;

    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

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

function speakText(text, pitch = 1.0, callback) {
    const ttsEnabled = document.getElementById('toggle-tts')?.checked;
    if (!ttsEnabled || !synth || text === "👍") {
        if (callback) setTimeout(callback, 500);
        return;
    }

    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const viVoice = voices.find(v => v.lang.includes('vi') || v.name.includes('Vietnamese') || v.name.includes('HoaiMy') || v.name.includes('NamMinh'));
    if (viVoice) {
        utterance.voice = viVoice;
    }

    utterance.pitch = pitch;
    utterance.rate = 1.12;

    utterance.onend = () => { if (callback) callback(); };
    utterance.onerror = () => { if (callback) callback(); };

    synth.speak(utterance);

    const estimatedDuration = Math.max(1500, text.length * 75);
    let called = false;
    const origEnd = utterance.onend;
    utterance.onend = () => {
        if (!called) {
            called = true;
            if (origEnd) origEnd();
        }
    };
    setTimeout(() => {
        if (!called && synth.speaking) {
            called = true;
            if (callback) callback();
        }
    }, estimatedDuration + 800);
}

function renderPhoneHeader() {
    const data = scenarios[currentScenarioKey];
    if (!data) return;

    const { owner } = getScenarioParticipants(data);
    const headerAvatar = document.querySelector('.messenger-header .avatar');
    const headerName = document.querySelector('.messenger-header .name');

    if (headerAvatar) headerAvatar.src = owner.avatar;
    if (headerName) headerName.textContent = owner.name;
    
    resetChat();
}

const THUMBS_UP_SVG = `<svg viewBox="0 0 24 24"><path d="M2.3 10.5c0-.83.67-1.5 1.5-1.5h1.7c.83 0 1.5.67 1.5 1.5v9c0 .83-.67 1.5-1.5 1.5H3.8c-.83 0-1.5-.67-1.5-1.5v-9z M8.5 19.5V10.8l2.9-4.2c.4-.6 1.1-1.1 1.8-1.4.5-.2 1.1-.2 1.5.1.5.3.8.9.8 1.5v3.2h3.3c1.7 0 3.1 1.3 3.2 3 .1.9-.3 1.7-.9 2.3.4.6.4 1.4.1 2.1-.3.6-.8 1-1.3 1.2.3.5.3 1.2 0 1.8-.4.7-1.1 1.1-1.9 1.1H11c-1.4 0-2.5-1.1-2.5-2.5z"/></svg>`;
const SEND_ARROW_SVG = `<svg viewBox="0 0 24 24"><path d="M3.4 20.4l17.4-7.8c.8-.4.8-1.5 0-1.8L3.4 3.1c-.8-.3-1.6.4-1.4 1.3L3.7 11c.1.3.4.6.7.6h7.1c.4 0 .7.3.7.7s-.3.7-.7.7H4.4c-.4 0-.7.2-.7.6L2 19.1c-.2.9.6 1.6 1.4 1.3z"/></svg>`;

function setSendButtonIcon(isTyping) {
    const sendBtn = document.getElementById('send-btn');
    if (!sendBtn) return;
    if (isTyping) {
        sendBtn.innerHTML = SEND_ARROW_SVG;
    } else {
        sendBtn.innerHTML = THUMBS_UP_SVG;
    }
}

function resetChat() {
    isPlaying = false;
    if (synth) synth.cancel();
    
    const chatWindow = document.getElementById('chat-window');
    const groupWindow = document.getElementById('group-chat-window');
    if (groupWindow) {
        groupWindow.innerHTML = '';
    }

    const data = scenarios[currentScenarioKey];
    if (!data || !chatWindow) return;
    
    const { owner, customer } = getScenarioParticipants(data);
    
    chatWindow.innerHTML = `
        <div class="chat-intro-banner">
            <img class="intro-avatar" src="${owner.avatar}" alt="Avatar" onerror="this.src='assets/owner_avatar.png'">
            <div class="intro-name">${owner.name}</div>
            <div class="intro-sub">Các bạn là bạn bè trên Facebook • Tài khoản kinh doanh</div>
            <div class="intro-time-divider">Hôm nay 22:30</div>
        </div>
    `;
    
    const typingRow = document.createElement('div');
    typingRow.className = 'typing-indicator-row';
    typingRow.id = 'typing-indicator';
    typingRow.innerHTML = `
        <img class="avatar-small" src="${customer.avatar}" alt="Avatar" onerror="this.src='assets/customer_avatar.png'">
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
        <img class="seen-avatar-tiny" src="${customer.avatar}" alt="Seen" onerror="this.src='assets/customer_avatar.png'">
    `;
    chatWindow.appendChild(seenRow);

    const inputText = document.getElementById('input-text');
    if (inputText) {
        inputText.textContent = 'Aa';
        inputText.classList.add('empty');
    }
    setSendButtonIcon(false);
    
    const btnPlay = document.getElementById('btn-play');
    if (btnPlay) {
        btnPlay.innerHTML = '<i class="fas fa-play"></i> ▶ Bắt Đầu Phát Demo (Auto Play)';
        btnPlay.classList.remove('playing');
    }
}

function typeInInput(text, duration, callback) {
    if (text === "👍") {
        if (callback) setTimeout(callback, 300);
        return;
    }

    const inputText = document.getElementById('input-text');
    if (!inputText) {
        if (callback) callback();
        return;
    }
    inputText.classList.remove('empty');
    inputText.textContent = "";
    setSendButtonIcon(true);
    
    let i = 0;
    // Tăng tốc độ gõ chữ: Giảm interval xuống rất thấp (25ms max) và dựa vào text length
    const intervalTime = Math.min(25, (duration * 0.7) / text.length);
    const timer = setInterval(() => {
        if (i < text.length) {
            inputText.textContent += text[i];
            i++;
        } else {
            clearInterval(timer);
            setTimeout(() => {
                inputText.textContent = "Aa";
                inputText.classList.add('empty');
                setSendButtonIcon(false);
                if (callback) callback();
            }, 250);
        }
    }, intervalTime);
}

function appendMessage(msg) {
    if (currentStudioMode === 'group') {
        const groupWindow = document.getElementById('group-chat-window');
        if (!groupWindow) return;

        let char = characterRoster.find(c => c.id === msg.senderId) ||
                   characterRoster.find(c => c.name === msg.senderName) ||
                   characterRoster[0];

        const senderName = msg.senderName || char.name;
        const avatar = char.avatar || 'assets/customer_avatar.png';

        const row = document.createElement('div');
        row.className = 'group-message-row';

        let bubbleHtml = '';
        if (msg.type === 'text') {
            bubbleHtml = `<div class="bubble-group-pink">${msg.content}</div>`;
        } else if (msg.type === 'product_card' || msg.type === 'product') {
            bubbleHtml = `
                <div class="bubble bubble-product">
                    <div class="product-image-container">
                        <img src="${msg.image || 'assets/vitamin_c.png'}" alt="Product">
                        <span class="product-badge">${msg.discount || 'SIÊU HOT'}</span>
                    </div>
                    <div class="product-meta-box">
                        <span class="product-shop-tag">TIKTOK SHOP • MUA NGAY KẺO HẾT</span>
                        <div class="product-title">${msg.content}</div>
                        <div class="product-price-row">
                            <span class="product-price">${msg.price || '99.000₫'}</span>
                        </div>
                        <button class="product-cta-btn">${msg.cta || '🛍 Xem Cửa Hàng / Chốt Đơn'}</button>
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
            <img class="group-avatar-small" src="${avatar}" alt="${senderName}" onerror="this.src='assets/customer_avatar.png'">
            <div class="group-message-body">
                <div class="group-sender-name">${senderName}</div>
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
    
    seenIndicator.classList.remove('active');

    const { customer } = getScenarioParticipants(data);
    const isCustomer = msg.sender === 'customer';
    const row = document.createElement('div');
    row.className = `message-row ${isCustomer ? 'left' : 'right'}`;

    let avatarHtml = isCustomer ? `<img class="avatar-small" src="${customer.avatar}" alt="Avatar" onerror="this.src='assets/customer_avatar.png'">` : '';
    let bubbleHtml = '';

    if (msg.type === 'text') {
        bubbleHtml = `<div class="bubble">${msg.content}</div>`;
    } else if (msg.type === 'product_card' || msg.type === 'product') {
        bubbleHtml = `
            <div class="bubble bubble-product">
                <div class="product-image-container">
                    <img src="${msg.image || 'assets/vitamin_c.png'}" alt="Product">
                    <span class="product-badge">${msg.discount || 'SIÊU HOT'}</span>
                </div>
                <div class="product-meta-box">
                    <span class="product-shop-tag">TIKTOK SHOP • MUA NGAY KẺO HẾT</span>
                    <div class="product-title">${msg.content}</div>
                    <div class="product-price-row">
                        <span class="product-price">${msg.price || '99.000₫'}</span>
                    </div>
                    <button class="product-cta-btn">${msg.cta || '🛍 Xem Cửa Hàng / Chốt Đơn'}</button>
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

    if (!isCustomer) {
        const statusText = document.getElementById('seen-status-text');
        if (msg.type === 'like_sticker') {
            if (statusText) statusText.textContent = "Đã gửi";
        } else {
            if (statusText) statusText.textContent = "Đã xem";
        }
        setTimeout(() => {
            seenIndicator.classList.add('active');
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }, 600);
    }

    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function runScenario() {
    if (isPlaying) {
        isPlaying = false;
        if (synth) synth.cancel();
        document.getElementById('btn-play').innerHTML = '▶ Tiếp Tục Phát';
        return;
    }

    initAudio();
    isPlaying = true;
    document.getElementById('btn-play').innerHTML = '⏸ Tạm Dừng Demo';
    
    const data = scenarios[currentScenarioKey];
    const messages = data.messages;
    const { owner, customer } = getScenarioParticipants(data);
    
    const selector = currentStudioMode === 'group' ? '.group-message-row' : '.message-row';
    const existingMessages = document.querySelectorAll(selector).length;
    let index = existingMessages;

    if (index >= messages.length) {
        resetChat();
        isPlaying = true;
        document.getElementById('btn-play').innerHTML = '⏸ Tạm Dừng Demo';
        index = 0;
    }

    function playNext() {
        if (!isPlaying || index >= messages.length) {
            isPlaying = false;
            document.getElementById('btn-play').innerHTML = '🔄 Phát Lại Từ Đầu';
            return;
        }

        const msg = messages[index];

        if (currentStudioMode === 'group') {
            const speaker = characterRoster.find(c => c.id === msg.senderId) || 
                            characterRoster.find(c => c.name === msg.senderName) || 
                            characterRoster[0];
            const groupWin = document.getElementById('group-chat-window');
            if (groupWin) groupWin.scrollTop = groupWin.scrollHeight;

            setTimeout(() => {
                appendMessage(msg);
                playSFX(msg.sfx || 'ting');

                const pitch = speaker ? speaker.pitch : 1.1;
                speakText(msg.content, pitch, () => {
                    index++;
                    setTimeout(playNext, 250);
                });
            }, msg.delay || 1200);
            return;
        }

        const isCustomer = msg.sender === 'customer';
        const typingIndicator = document.getElementById('typing-indicator');

        if (isCustomer) {
            document.getElementById('chat-window').scrollTop = document.getElementById('chat-window').scrollHeight;

            setTimeout(() => {
                appendMessage(msg);
                playSFX(msg.sfx || 'ting');

                const pitch = customer.pitch || 1.2;
                speakText(msg.content, pitch, () => {
                    index++;
                    setTimeout(playNext, 250);
                });
            }, msg.delay || 1200);
        } else {
            setTimeout(() => {
                appendMessage(msg);
                playSFX(msg.sfx || 'pop');

                const pitch = owner.pitch || 0.95;
                speakText(msg.content, pitch, () => {
                    index++;
                    setTimeout(playNext, 250);
                });
            }, msg.delay || 1500);
        }
    }

    playNext();
}

function selectScenario(key) {
    if (!scenarios[key]) return;
    currentScenarioKey = key;
    
    document.querySelectorAll('.scenario-card').forEach(card => {
        card.classList.remove('active');
    });
    const selected = document.getElementById(`card-${key}`);
    if (selected) selected.classList.add('active');

    const jsonEditor = document.getElementById('json-editor');
    if (jsonEditor) jsonEditor.value = JSON.stringify(scenarios[key], null, 2);

    if (scenarios[key].theme === 'group_messenger' || currentStudioMode === 'group') {
        renderGroupHeader();
    } else {
        renderPhoneHeader();
    }
    renderScriptBuilder();
    resetChat();
    renderAllMessagesInstant();
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

    if (tabCards) tabCards.style.display = 'none';
    if (tabBuilder) tabBuilder.style.display = 'none';
    if (tabChars) tabChars.style.display = 'none';
    if (tabJson) tabJson.style.display = 'none';

    if (btnCards) btnCards.classList.remove('active');
    if (btnBuilder) btnBuilder.classList.remove('active');
    if (btnChars) btnChars.classList.remove('active');
    if (btnJson) btnJson.classList.remove('active');

    if (tabName === 'cards') {
        if (tabCards) tabCards.style.display = 'block';
        if (btnCards) btnCards.classList.add('active');
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
        scenarios[currentScenarioKey] = parsed;
        renderPhoneHeader();
        renderScriptBuilder();
        resetChat();
        renderAllMessagesInstant();
        alert("🎉 Đã áp dụng kịch bản mới! Toàn bộ đoạn chat đã hiện lên màn hình, bạn có thể bấm 'Chụp Ảnh Giao Diện' ngay.");
    } catch (e) {
        alert("⚠️ Lỗi cú pháp JSON: " + e.message);
    }
}


function updateClock() {
    const clockEl = document.getElementById('phone-time');
    if (!clockEl) return;
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    clockEl.textContent = `${h}:${m}`;
}

window.addEventListener('DOMContentLoaded', async () => {
    // ---- Khởi tạo IndexedDB & Migration ----
    try {
        const migratedChars = await migrateFromLocalStorage();
        if (migratedChars && migratedChars.length > 0) {
            characterRoster = migratedChars;
            console.log('✅ Loaded', characterRoster.length, 'characters from IndexedDB');
        } else {
            // Không có dữ liệu cũ — lưu mặc định vào IndexedDB
            await saveCharactersToIndexedDB(defaultCharacters);
            characterRoster = [...defaultCharacters];
        }
        _dbReady = true;
    } catch (e) {
        console.warn('IndexedDB init failed, using defaults:', e);
        characterRoster = [...defaultCharacters];
    }

    // ---- Render giao diện ----
    renderCharacterRoster();
    const urlParams = new URLSearchParams(window.location.search);
    const modeParam = urlParams.get('mode');
    if (modeParam === 'group') {
        switchStudioMode('group');
    } else if (modeParam === 'fb') {
        switchStudioMode('fb');
    } else {
        selectScenario('scenario_1');
    }
    updateClock();
    setInterval(updateClock, 15000);

    const avatarInput = document.getElementById('char-input-avatar-file');
    if (avatarInput) {
        avatarInput.addEventListener('change', (e) => handleAvatarFileSelect(e.target));
    }
});

// ============================================================================
// 6. LOGIC GROUP CHAT (PET BITE) & FACEBOOK POST MODE
// ============================================================================

let currentStudioMode = 'chat'; // 'chat', 'group', or 'fb'
let groupChatSettings = {
    name: "Văn Phòng Cửa Thép Luxury",
    unread: 8,
    avatar: "assets/steel_door_logo.png",
    wallpaper: "assets/bg_anime_sky.jpg",
    bubbleColor: "#e0f2fe"
};

function switchStudioMode(mode) {
    currentStudioMode = mode;
    
    // Nút Tab Active
    const btnChat = document.getElementById('btn-mode-chat');
    const btnGroup = document.getElementById('btn-mode-group');
    const btnFb = document.getElementById('btn-mode-fb');

    if (btnChat) btnChat.className = mode === 'chat' ? 'btn-primary' : 'btn-secondary';
    if (btnGroup) btnGroup.className = mode === 'group' ? 'btn-primary' : 'btn-secondary';
    if (btnFb) btnFb.className = mode === 'fb' ? 'btn-primary' : 'btn-secondary';
    
    // Panel Trái
    const panelChat = document.getElementById('panel-chat-mode');
    const panelGroup = document.getElementById('panel-group-mode');
    const panelFb = document.getElementById('panel-fb-mode');

    if (panelChat) panelChat.style.display = (mode === 'chat' || mode === 'group') ? 'block' : 'none';
    if (panelGroup) panelGroup.style.display = mode === 'group' ? 'flex' : 'none';
    if (panelFb) panelFb.style.display = mode === 'fb' ? 'flex' : 'none';
    
    // Panel Giữa (Preview Stage)
    const frameChat = document.getElementById('frame-chat-mode');
    const frameGroup = document.getElementById('frame-group-mode');
    const frameFb = document.getElementById('frame-fb-mode');

    if (frameChat) frameChat.style.display = mode === 'chat' ? 'flex' : 'none';
    if (frameGroup) frameGroup.style.display = mode === 'group' ? 'flex' : 'none';
    if (frameFb) frameFb.style.display = mode === 'fb' ? 'flex' : 'none';

    // Panel Phải (Ẩn Play Demo bên FB Mode vì FB tĩnh)
    const playGroup = document.querySelector('.control-group');
    if (playGroup) {
        playGroup.style.display = (mode === 'chat' || mode === 'group') ? 'block' : 'none';
    }

    if (mode === 'group') {
        const targetKey = 'scenario_group_cuathep';
        if (currentScenarioKey !== targetKey && scenarios[targetKey]) {
            selectScenario(targetKey);
        } else {
            renderGroupHeader();
            resetChat();
            renderAllMessagesInstant();
        }
    } else if (mode === 'chat') {
        if (currentScenarioKey === 'scenario_group_cuathep' || currentScenarioKey === 'scenario_group_petbite') {
            selectScenario('scenario_1');
        } else {
            renderPhoneHeader();
            resetChat();
            renderAllMessagesInstant();
        }
    } else if (mode === 'fb') {
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
    }

    const bColor = sc?.bubbleColor || groupChatSettings.bubbleColor;
    if (groupWin) {
        groupWin.style.setProperty('--group-bubble-color', bColor);
    }
}

function updateGroupHeaderFromInputs() {
    const nameInput = document.getElementById('group-name-input');
    const unreadInput = document.getElementById('group-unread-input');
    if (nameInput) {
        const val = nameInput.value.trim() || 'Văn phòng Pet Bite';
        groupChatSettings.name = val;
        if (scenarios[currentScenarioKey]) scenarios[currentScenarioKey].groupName = val;
        const nameEl = document.getElementById('group-render-name');
        if (nameEl) nameEl.textContent = val;
    }
    if (unreadInput) {
        const val = parseInt(unreadInput.value) || 0;
        groupChatSettings.unread = val;
        if (scenarios[currentScenarioKey]) scenarios[currentScenarioKey].groupUnread = val;
        const unreadEl = document.getElementById('group-unread-badge');
        if (unreadEl) unreadEl.textContent = val;
    }
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
}

function handleGroupBgUpload(input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            setGroupWallpaper(e.target.result, 'custom');
        };
        reader.readAsDataURL(file);
    }
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
}

function handleGroupAvatarUpload(input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            groupChatSettings.avatar = e.target.result;
            if (scenarios[currentScenarioKey]) scenarios[currentScenarioKey].groupAvatar = e.target.result;
            const avatarEl = document.getElementById('group-render-avatar');
            if (avatarEl) avatarEl.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
}

function loadCuaThepScenario() {
    const key = scenarios['scenario_group_cuathep'] ? 'scenario_group_cuathep' : 'scenario_group_petbite';
    if (scenarios[key]) {
        switchStudioMode('group');
        selectScenario(key);
        switchTab('builder');
    }
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
    }
    renderScriptBuilder();
    resetChat();
    renderAllMessagesInstant();
}

function renderFbPost() {
    const author = document.getElementById('fb-author-name').value;
    const content = document.getElementById('fb-post-content').value;
    const likes = document.getElementById('fb-likes').value;
    const comments = document.getElementById('fb-comments').value;
    
    document.getElementById('fb-render-name').textContent = author || 'Người dùng ẩn danh';
    document.getElementById('fb-render-content').textContent = content;
    document.getElementById('fb-render-likes').textContent = likes;
    document.getElementById('fb-render-comments').textContent = comments;
}

function handleFbAvatarUpload(input) {
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('fb-render-avatar').src = e.target.result;
        }
        reader.readAsDataURL(file);
    }
}

function handleFbImageUpload(input) {
    const file = input.files[0];
    const container = document.getElementById('fb-render-image-container');
    const img = document.getElementById('fb-render-image');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            img.src = e.target.result;
            container.style.display = 'flex';
        }
        reader.readAsDataURL(file);
    } else {
        container.style.display = 'none';
        img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
    }
}

// ============================================================================
// 7. HỖ TRỢ ĐIỀU HƯỚNG TRÊN THIẾT BỊ DI ĐỘNG (SMARTPHONE TAB NAVIGATION)
// ============================================================================
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
        if (leftPanel) leftPanel.style.display = (currentStudioMode === 'fb') ? 'none' : 'block';
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
        alert('Đường dẫn: ' + text);
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

