#!/usr/bin/env node
import { V3 } from " @browserbasehq/stagehand/dist/esm/lib/v3/v3.js\;

const DEFAULT_URL = \http://127.0.0.1:5173\;
const DEFAULT_SELECTOR = \#root\;
const [requestedUrl, requestedSelector] = process.argv.slice(2);
const targetUrl = requestedUrl || process.env.STAGEHAND_UI_URL || DEFAULT_URL;
const selector = requestedSelector || process.env.STAGEHAND_UI_SELECTOR || DEFAULT_SELECTOR;
const stagehand = new V3({
 env: \LOCAL\,
 disableAPI: true,
 verbose: 0,
 localBrowserLaunchOptions: {
 headless: process.env.STAGEHAND_UI_HEADLESS !== \false\,
 args: [
 \--no-sandbox\,
 \--disable-setuid-sandbox\,
 \--disable-gpu\,
 \--disable-dev-shm-usage\,
 ],
 viewport: { width: 1280, height: 800 },
 userDataDir: process.env.STAGEHAND_UI_PROFILE,
 },
});

async function run() {
 try {
 await stagehand.init();
 const ctx = stagehand.context;
 if (!ctx) {
 throw new Error(\Stagehand context unavailable after init\);
 }
 const page = await ctx.newPage(targetUrl);
 await page.waitForLoadState(\load\, 15000);
 await page.waitForSelector(selector, { timeout: 10000 });
 console.log(
 Stagehand QA passed: selector is present on ,
 );
 } finally {
 await stagehand.close({ force: true }).catch(() => { /* best effort */ });
 }
}

run().catch((error) => {
 console.error(\Stagehand QA runner failed:\, error);
 process.exit(1);
});
