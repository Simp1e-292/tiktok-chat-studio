const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

async function renderChatFrames(outputDir) {
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    console.log('[RenderFrames] Launching headless Chromium...');
    const browser = await puppeteer.launch({
        executablePath: '/usr/bin/chromium',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--ignore-certificate-errors',
            '--allow-file-access-from-files'
        ]
    });

    const page = await browser.newPage();
    // Use high resolution for crisp 9:16 phone mockup
    await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 2 });

    const htmlPath = path.resolve(__dirname, 'index.html');
    const fileUrl = `file://${htmlPath}?mode=group`;
    console.log('[RenderFrames] Loading page:', fileUrl);
    await page.goto(fileUrl, { waitUntil: 'load' });
    await new Promise(r => setTimeout(r, 800));

    // Ensure group mode is active and reset chat
    await page.evaluate(() => {
        if (typeof switchStudioMode === 'function') switchStudioMode('group');
        if (typeof selectScenario === 'function') selectScenario('scenario_group_cuathep');
        if (typeof resetChat === 'function') resetChat();
    });
    await new Promise(r => setTimeout(r, 600));

    const selector = '.phone-frame';
    const phoneEl = await page.$(selector);
    if (!phoneEl) {
        throw new Error(`Element ${selector} not found on page!`);
    }

    // Step 0: Header & Empty chat wallpaper
    const frame0Path = path.join(outputDir, 'frame_0.png');
    await phoneEl.screenshot({ path: frame0Path });
    console.log('[RenderFrames] Saved frame_0.png');

    const messages = await page.evaluate(() => {
        return scenarios['scenario_group_cuathep'].messages;
    });
    console.log(`[RenderFrames] Found ${messages.length} messages in scenario.`);

    const frameList = [{ index: 0, file: 'frame_0.png', message: null }];

    for (let i = 0; i < messages.length; i++) {
        const msg = messages[i];
        await page.evaluate((m) => {
            appendMessage(m);
        }, msg);

        // Wait for rendering & smooth scroll
        await new Promise(r => setTimeout(r, 250));

        const fileName = `frame_${i + 1}.png`;
        const filePath = path.join(outputDir, fileName);
        await phoneEl.screenshot({ path: filePath });
        console.log(`[RenderFrames] Saved ${fileName} for message [${msg.id || i}]: "${msg.content ? msg.content.substring(0, 30) : ''}..."`);

        frameList.push({
            index: i + 1,
            file: fileName,
            message: msg
        });
    }

    await browser.close();
    console.log(`[RenderFrames] Completed! Rendered ${frameList.length} frames into ${outputDir}`);

    const manifestPath = path.join(outputDir, 'frames_manifest.json');
    fs.writeFileSync(manifestPath, JSON.stringify(frameList, null, 2), 'utf8');
    return frameList;
}

if (require.main === module) {
    const targetDir = process.argv[2] || path.join(__dirname, 'draft_frames');
    renderChatFrames(targetDir)
        .then(() => process.exit(0))
        .catch(err => {
            console.error('[RenderFrames] Error:', err);
            process.exit(1);
        });
}

module.exports = { renderChatFrames };
