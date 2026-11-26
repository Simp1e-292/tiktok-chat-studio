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
        ]
        : ['/usr/bin/chromium', '/usr/bin/google-chrome'];
    for (const p of candidates) {
        if (fs.existsSync(p)) return p;
    }
    throw new Error('Không tìm thấy Chrome hoặc Edge!');
}

async function waitForImages(page) {
    await page.evaluate(async () => {
        const imgs = Array.from(document.querySelectorAll('img'));
        await Promise.all(imgs.map(img => {
            if (img.complete && img.naturalWidth > 0) return Promise.resolve();
            return new Promise(res => {
                img.onload = res;
                img.onerror = res;
                setTimeout(res, 1500);
            });
        }));
    });
}

async function renderFrames(outputDir, manifestPath, stageHtmlPath) {
    fs.mkdirSync(outputDir, { recursive: true });
    const items = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

    let curr = 0.0;
    const events = [];
    for (const it of items) {
        const hasTyping = Boolean(it.typing) && curr >= 0.8;
        if (hasTyping) {
            const typingDur = Number((it.typing_dur !== undefined ? it.typing_dur : 0.24).toFixed(3));
            events.push({
                time: Number(curr.toFixed(3)),
                duration: typingDur,
                action: 'typing',
                item: it,
                banner: curr >= 3.8 ? 'series' : 'hook',
                is_gif: false,
            });
            curr += typingDur;
        }

        let itemDur = 0.0;
        if (it.kind === 'msg') {
            const hasVisual = Boolean(it.img || it.meme_gif || it.screenshot_quote);
            const vDelay = it.voice_delay !== undefined ? it.voice_delay : 0.08;
            const postGap = it.post_gap !== undefined ? it.post_gap : (hasVisual ? 0.72 : 0.40);
            itemDur = Number((vDelay + it.duration_sec + postGap + (it.extra_pause || 0)).toFixed(3));
        } else if (it.kind === 'end_card' && it.duration_sec) {
            const vDelay = it.voice_delay !== undefined ? it.voice_delay : 0.08;
            const postGap = it.post_gap !== undefined ? it.post_gap : 1.45;
            itemDur = Number((vDelay + it.duration_sec + postGap).toFixed(3));
        } else {
            itemDur = Number((it.hold || 1.45).toFixed(3));
        }

        events.push({
            time: Number(curr.toFixed(3)),
            duration: itemDur,
            action: 'item',
            item: it,
            banner: curr >= 3.8 ? 'series' : 'hook',
            is_gif: Boolean(it.meme_gif),
        });
        curr += itemDur;
    }

    const browser = await puppeteer.launch({
        executablePath: resolveBrowserExecutable(),
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--allow-file-access-from-files']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });

    const stageUrl = pathToFileURL(path.resolve(stageHtmlPath)).href;
    await page.goto(stageUrl, { waitUntil: 'load' });
    await new Promise(r => setTimeout(r, 400));

    const timelineOut = [];
    for (let i = 0; i < events.length; i++) {
        const ev = events[i];
        await page.evaluate((e) => {
            setBannerMode(e.banner);
            if (e.action === 'typing') {
                showTyping(e.item);
            } else {
                applyItem(e.item);
            }
        }, ev);

        await waitForImages(page);
        await new Promise(r => setTimeout(r, 80));

        const frames = [];
        if (ev.is_gif) {
            for (let f = 0; f < 10; f++) {
                const fn = `ev_${String(i).padStart(2, '0')}_f${String(f).padStart(2, '0')}.png`;
                await page.screenshot({ path: path.join(outputDir, fn) });
                frames.push(fn);
                await new Promise(r => setTimeout(r, 85));
            }
        } else {
            const fn = `ev_${String(i).padStart(2, '0')}.png`;
            await page.screenshot({ path: path.join(outputDir, fn) });
            frames.push(fn);
        }

        timelineOut.push({
            ev_index: i,
            time: ev.time,
            duration: ev.duration,
            action: ev.action,
            item_idx: ev.item.idx,
            frames,
        });
        console.log(`[RenderHoCaKoi] ev=${i} t=${ev.time.toFixed(2)}s dur=${ev.duration.toFixed(2)}s action=${ev.action} #${ev.item.idx} (${ev.item.kind})`);
    }

    fs.writeFileSync(path.join(outputDir, 'events_timeline.json'), JSON.stringify(timelineOut, null, 2), 'utf8');
    await browser.close();
    console.log(`[RenderHoCaKoi] Hoàn tất! Tổng thời lượng: ${curr.toFixed(2)}s`);
}

if (require.main === module) {
    const outDir = path.resolve(process.argv[2] || path.join(__dirname, 'ho_ca_koi_frames'));
    const manifest = path.resolve(process.argv[3] || path.join(__dirname, 'conbo_ho_ca_koi_voices', 'manifest.json'));
    const stageHtml = path.resolve(process.argv[4] || path.join(__dirname, 'render_ho_ca_koi_stage.html'));
    renderFrames(outDir, manifest, stageHtml)
        .then(() => process.exit(0))
        .catch(err => {
            console.error(err);
            process.exit(1);
        });
}
