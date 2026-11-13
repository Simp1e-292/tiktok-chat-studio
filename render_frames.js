const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');

function resolveBrowserExecutable() {
    if (process.env.CHROME_PATH && fs.existsSync(process.env.CHROME_PATH)) {
        return process.env.CHROME_PATH;
    }
    let candidates = [];
    if (process.platform === 'win32') {
        candidates = [
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
            path.join(process.env.LOCALAPPDATA || '', 'Google\\Chrome\\Application\\chrome.exe'),
            'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
            'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
            path.join(process.env.LOCALAPPDATA || '', 'Microsoft\\Edge\\Application\\msedge.exe'),
            path.join(process.env.LOCALAPPDATA || '', 'CocCoc\\Browser\\Application\\browser.exe')
        ];
    } else if (process.platform === 'darwin') {
        candidates = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
            '/Applications/Chromium.app/Contents/MacOS/Chromium'
        ];
    } else {
        candidates = ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable'];
    }

    for (const p of candidates) {
        if (p && fs.existsSync(p)) return p;
    }
    throw new Error('Không tìm thấy trình duyệt Chrome/Edge/Chromium trên máy! Hãy cài Chrome hoặc đặt biến môi trường CHROME_PATH.');
}

async function waitForImages(page, selector) {
    await page.evaluate(async (sel) => {
        const root = document.querySelector(sel);
        if (!root) return;
        if (document.fonts && document.fonts.ready) {
            await document.fonts.ready;
        }
        const imgs = Array.from(root.querySelectorAll('img'));
        await Promise.all(imgs.map(img => {
            if (img.complete) return Promise.resolve();
            return new Promise(resolve => {
                const done = () => resolve();
                img.addEventListener('load', done, { once: true });
                img.addEventListener('error', done, { once: true });
                setTimeout(done, 2500);
            });
        }));
    }, selector);
}

async function renderChatFrames(outputDir, scenarioArg = 'scenario_group_cuathep') {
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    let customPayload = null;
    let scenarioKey = 'scenario_group_cuathep';

    if (scenarioArg && fs.existsSync(scenarioArg) && fs.statSync(scenarioArg).isFile()) {
        const raw = fs.readFileSync(scenarioArg, 'utf8');
        const parsed = JSON.parse(raw);
        if (parsed && parsed.scenario) {
            customPayload = parsed;
            scenarioKey = parsed.scenarioKey || 'scenario_custom_render';
        } else {
            customPayload = { scenario: parsed, scenarioKey: 'scenario_custom_render' };
            scenarioKey = 'scenario_custom_render';
        }
        console.log(`[RenderFrames] Loaded custom scenario JSON from: ${scenarioArg}`);
    } else if (scenarioArg) {
        scenarioKey = scenarioArg;
    }

    const executablePath = resolveBrowserExecutable();
    console.log('[RenderFrames] Launching headless browser:', executablePath);
    const browser = await puppeteer.launch({
        executablePath,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--ignore-certificate-errors',
            '--allow-file-access-from-files'
        ]
    });

    try {
        const page = await browser.newPage();
        await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 2 });

        const htmlPath = path.resolve(__dirname, 'index.html');
        const fileUrl = `${pathToFileURL(htmlPath).href}?render=1`;
        console.log('[RenderFrames] Loading page:', fileUrl);
        await page.goto(fileUrl, { waitUntil: 'load' });
        await new Promise(r => setTimeout(r, 600));

        // Inject custom characters & scenario if supplied, and configure clean transparent framing
        const setupInfo = await page.evaluate((payload, targetKey) => {
            if (payload) {
                if (Array.isArray(payload.characters) && payload.characters.length > 0) {
                    characterRoster = payload.characters;
                }
                if (payload.scenario) {
                    scenarios[targetKey] = payload.scenario;
                }
            }

            const sc = scenarios[targetKey];
            if (!sc) {
                throw new Error(`Không tìm thấy kịch bản '${targetKey}' trong Studio!`);
            }

            const isGroup = (sc.theme === 'group_messenger') || (payload && payload.mode === 'group');
            const targetMode = isGroup ? 'group' : 'chat';

            // Ngăn đồng hồ thay đổi giữa chừng trong lúc render từng frame
            const clockEl = document.getElementById('phone-time');
            if (clockEl) {
                clockEl.textContent = (sc.clockTime || '10:19');
            }
            window.updateClock = function () {};

            // Làm nền ngoài trong suốt để cắt bo góc iPhone chuẩn không bị viền trắng
            document.documentElement.style.background = 'transparent';
            document.body.style.background = 'transparent';
            const stage = document.querySelector('.preview-stage');
            if (stage) stage.style.background = 'transparent';
            const glow = document.querySelector('.stage-glow');
            if (glow) glow.style.display = 'none';
            const phone = document.querySelector('.phone-frame');
            if (phone) {
                phone.style.border = 'none';
                phone.style.boxShadow = 'none';
                phone.style.borderRadius = '24px';
            }

            currentStudioMode = targetMode;
            currentScenarioKey = targetKey;

            const frameChat = document.getElementById('frame-chat-mode');
            const frameGroup = document.getElementById('frame-group-mode');
            const frameFb = document.getElementById('frame-fb-mode');
            if (frameChat) frameChat.style.display = targetMode === 'chat' ? 'flex' : 'none';
            if (frameGroup) frameGroup.style.display = targetMode === 'group' ? 'flex' : 'none';
            if (frameFb) frameFb.style.display = 'none';

            if (targetMode === 'group') {
                if (typeof renderGroupHeader === 'function') renderGroupHeader();
            } else {
                if (typeof renderPhoneHeader === 'function') renderPhoneHeader();
            }
            if (typeof resetChat === 'function') resetChat();

            return {
                mode: targetMode,
                title: sc.title || targetKey,
                messages: sc.messages || []
            };
        }, customPayload, scenarioKey);

        const selector = '.phone-frame';
        const phoneEl = await page.$(selector);
        if (!phoneEl) {
            throw new Error(`Không tìm thấy phần tử ${selector} trên trang!`);
        }

        await waitForImages(page, selector);
        await new Promise(r => setTimeout(r, 300));

        // Step 0: Header & Empty chat screen
        const frame0Path = path.join(outputDir, 'frame_0.png');
        await phoneEl.screenshot({ path: frame0Path, omitBackground: true });
        console.log('[RenderFrames] Saved frame_0.png');

        const messages = setupInfo.messages;
        console.log(`[RenderFrames] Mode=${setupInfo.mode}, Found ${messages.length} messages in scenario.`);

        const frameList = [{ index: 0, file: 'frame_0.png', message: null }];

        for (let i = 0; i < messages.length; i++) {
            const msg = messages[i];
            await page.evaluate((m, mode) => {
                appendMessage(m);
                if (mode === 'chat') {
                    const seen = document.getElementById('seen-indicator');
                    if (seen && m.sender !== 'customer') {
                        seen.classList.add('active');
                    }
                    const cw = document.getElementById('chat-window');
                    if (cw) cw.scrollTop = cw.scrollHeight;
                } else {
                    const gw = document.getElementById('group-chat-window');
                    if (gw) gw.scrollTop = gw.scrollHeight;
                }
            }, msg, setupInfo.mode);

            await waitForImages(page, selector);
            await new Promise(r => setTimeout(r, 150));

            const fileName = `frame_${i + 1}.png`;
            const filePath = path.join(outputDir, fileName);
            await phoneEl.screenshot({ path: filePath, omitBackground: true });
            const previewText = msg.content ? String(msg.content).substring(0, 32) : msg.type;
            console.log(`[RenderFrames] Saved ${fileName} [${msg.id || i}]: "${previewText}..."`);

            frameList.push({
                index: i + 1,
                file: fileName,
                message: msg
            });
        }

        console.log(`[RenderFrames] Completed! Rendered ${frameList.length} frames into ${outputDir}`);

        const manifestPath = path.join(outputDir, 'frames_manifest.json');
        fs.writeFileSync(manifestPath, JSON.stringify(frameList, null, 2), 'utf8');
        return frameList;
    } finally {
        await browser.close();
    }
}

if (require.main === module) {
    const targetDir = process.argv[2] || path.join(__dirname, 'draft_frames');
    const scenarioArg = process.argv[3] || 'scenario_group_cuathep';
    renderChatFrames(targetDir, scenarioArg)
        .then(() => process.exit(0))
        .catch(err => {
            console.error('[RenderFrames] Error:', err);
            process.exit(1);
        });
}

module.exports = { renderChatFrames };
