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
        const body = document.getElementById('chat-body');
        if (body) body.scrollTop = body.scrollHeight;
    });
}

async function renderV3Frames(outputDir, manifestPath) {
    fs.mkdirSync(outputDir, { recursive: true });
    const items = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

    // Xây dựng chuỗi sự kiện theo thời gian chính xác 0.0s -> 50.0s
    const events = [];
    for (const it of items) {
        if (it.typing && it.t >= 0.6) {
            events.push({ time: Number((it.t - 0.5).toFixed(2)), action: 'typing', item: it, banner: it.t - 0.5 >= 3.0 ? 'series' : 'hook', is_gif: false });
        }
        events.push({
            time: it.t,
            action: 'item',
            item: it,
            banner: it.t >= 3.0 ? 'series' : 'hook',
            is_gif: Boolean(it.meme_gif)
        });
    }
    events.sort((a, b) => a.time - b.time);

    // Gán duration cho từng segment, tổng = 50.00s
    const TOTAL_DUR = 50.0;
    for (let i = 0; i < events.length; i++) {
        const nextT = (i + 1 < events.length) ? events[i + 1].time : TOTAL_DUR;
        events[i].duration = Number((nextT - events[i].time).toFixed(3));
    }

    const browser = await puppeteer.launch({
        executablePath: resolveBrowserExecutable(),
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--allow-file-access-from-files']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });

    const stageUrl = pathToFileURL(path.resolve(__dirname, 'render_episode1_v3_stage.html')).href;
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
            frames
        });
        console.log(`[RenderV3] ev=${i} t=${ev.time}s dur=${ev.duration}s action=${ev.action} #${ev.item.idx} (${frames.length}f)`);
    }

    fs.writeFileSync(path.join(outputDir, 'events_timeline.json'), JSON.stringify(timelineOut, null, 2), 'utf8');
    await browser.close();
    console.log(`[RenderV3] Done! Total events: ${timelineOut.length}, Target duration: ${TOTAL_DUR}s`);
}

if (require.main === module) {
    const outDir = path.join(__dirname, 'episode1_v3_frames');
    const manifest = path.join(__dirname, 'vieneu_episode1_v3_voices', 'manifest.json');
    renderV3Frames(outDir, manifest)
        .then(() => process.exit(0))
        .catch(err => {
            console.error(err);
            process.exit(1);
        });
}
