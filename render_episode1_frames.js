const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');

function resolveBrowserExecutable() {
    if (process.env.CHROME_PATH && fs.existsSync(process.env.CHROME_PATH)) {
        return process.env.CHROME_PATH;
    }
    const candidates = process.platform === 'win32'
        ? [
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
            'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
            path.join(process.env.LOCALAPPDATA || '', 'Google\\Chrome\\Application\\chrome.exe')
        ]
        : ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome'];

    for (const p of candidates) {
        if (p && fs.existsSync(p)) return p;
    }
    throw new Error('Không tìm thấy trình duyệt Chrome/Edge/Chromium trên máy!');
}

function makeAvatarDataUri(initials, bgHex) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
        <rect width="128" height="128" rx="64" fill="${bgHex}"/>
        <text x="64" y="76" font-family="Segoe UI, Arial, sans-serif" font-size="48" font-weight="700" fill="#ffffff" text-anchor="middle">${initials}</text>
    </svg>`;
    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}

async function renderEpisode1Frames(outputDir, manifestPath) {
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const rawMessages = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    const messages = rawMessages.map(m => ({ ...m, type: m.type || 'text' }));

    const episodeCharacters = [
        { id: 'char_tien_hai',  name: 'Tiến Hải (CSKH)',      role: 'customer', pitch: 1.0, avatar: makeAvatarDataUri('TH', '#2563eb') },
        { id: 'char_truong',    name: 'Trưởng (Thiết kế)',    role: 'owner',    pitch: 1.0, avatar: makeAvatarDataUri('TR', '#1e293b') },
        { id: 'char_tung_anh',  name: 'Tùng anh (Thiết kế)',  role: 'customer', pitch: 1.0, avatar: makeAvatarDataUri('TA', '#0d9488') },
        { id: 'char_tung_em',   name: 'Tùng em (Thiết kế)',   role: 'customer', pitch: 1.0, avatar: makeAvatarDataUri('TE', '#16a34a') },
        { id: 'char_trang',     name: 'Trang (CSKH)',         role: 'customer', pitch: 1.0, avatar: makeAvatarDataUri('TG', '#db2777') },
        { id: 'char_nga_tk',    name: 'Nga (Thiết kế)',       role: 'customer', pitch: 1.0, avatar: makeAvatarDataUri('NG', '#7c3aed') },
        { id: 'char_thanh_hai', name: 'Thanh Hải (Kế toán)',  role: 'owner',    pitch: 1.0, avatar: makeAvatarDataUri('KT', '#d97706') },
        { id: 'char_minh_cham', name: 'Minh Châm (Mua hàng)', role: 'customer', pitch: 1.0, avatar: makeAvatarDataUri('MC', '#dc2626') },
        { id: 'char_kim',       name: 'Kim (Nhân sự)',        role: 'customer', pitch: 1.0, avatar: makeAvatarDataUri('KM', '#92400e') },
    ];

    const executablePath = resolveBrowserExecutable();
    console.log('[RenderEp1] Launching headless browser:', executablePath);
    const browser = await puppeteer.launch({
        executablePath,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--ignore-certificate-errors',
            '--allow-file-access-from-files'
        ]
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 2 });

    const htmlPath = path.resolve(__dirname, 'index.html');
    const fileUrl = `${pathToFileURL(htmlPath).href}?mode=group`;
    await page.goto(fileUrl, { waitUntil: 'load' });
    await new Promise(r => setTimeout(r, 800));

    await page.evaluate((chars, msgs) => {
        // Bơm danh sách 9 nhân vật Tập 1 vào characterRoster
        chars.forEach(c => {
            const idx = characterRoster.findIndex(x => x.id === c.id);
            if (idx >= 0) characterRoster[idx] = c;
            else characterRoster.push(c);
        });

        scenarios['scenario_episode_1'] = {
            title: '🚪 Cánh Cửa Khắc Tên Crush',
            theme: 'group_messenger',
            groupName: 'Văn Phòng Cửa Thép 🚪🔥',
            groupUnread: 13,
            groupAvatar: 'assets/steel_door_logo.png',
            bgWallpaper: 'assets/bg_anime_sky.jpg',
            bubbleColor: '#ffffff',
            messages: msgs
        };

        if (typeof switchStudioMode === 'function') switchStudioMode('group');
        if (typeof selectScenario === 'function') selectScenario('scenario_episode_1');
        if (typeof resetChat === 'function') resetChat();

        const gw = document.getElementById('group-chat-window');
        if (gw) gw.style.scrollBehavior = 'auto';
    }, episodeCharacters, messages);

    await new Promise(r => setTimeout(r, 600));

    const phoneEl = await page.$('.phone-frame');
    if (!phoneEl) {
        throw new Error('Không tìm thấy phần tử .phone-frame!');
    }

    // Frame 0: Khung trống đầu tập
    await phoneEl.screenshot({ path: path.join(outputDir, 'frame_0.png') });
    console.log('[RenderEp1] Saved frame_0.png (Intro)');

    for (let i = 0; i < messages.length; i++) {
        const msg = messages[i];
        await page.evaluate((m) => {
            appendMessage(m);
            const gw = document.getElementById('group-chat-window');
            if (gw) gw.scrollTop = gw.scrollHeight;
        }, msg);

        await new Promise(r => setTimeout(r, 300));
        const fileName = `frame_${i + 1}.png`;
        await phoneEl.screenshot({ path: path.join(outputDir, fileName) });
        console.log(`[RenderEp1] Saved ${fileName}: ${msg.senderName}`);
    }

    await browser.close();
    console.log(`[RenderEp1] Hoàn tất xuất ${messages.length + 1} khung hình vào ${outputDir}`);
}

if (require.main === module) {
    const baseDir = __dirname;
    const outputDir = process.argv[2] || path.join(baseDir, 'episode1_frames');
    const manifestPath = process.argv[3] || path.join(baseDir, 'elevenlabs_episode1_voices', 'manifest.json');
    renderEpisode1Frames(outputDir, manifestPath)
        .then(() => process.exit(0))
        .catch(err => {
            console.error('[RenderEp1] Error:', err);
            process.exit(1);
        });
}

module.exports = { renderEpisode1Frames };
