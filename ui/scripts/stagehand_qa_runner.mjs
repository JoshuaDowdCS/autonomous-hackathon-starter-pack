#!/usr/bin/env node
import { Stagehand } from "@browserbasehq/stagehand";

const DEFAULT_URL = "http://127.0.0.1:5173";
const DEFAULT_SELECTOR = "#root";
const [requestedUrl, requestedSelector] = process.argv.slice(2);
const targetUrl = requestedUrl || process.env.STAGEHAND_UI_URL || DEFAULT_URL;
const selector = requestedSelector || process.env.STAGEHAND_UI_SELECTOR || DEFAULT_SELECTOR;

const stagehand = new Stagehand({
  env: "LOCAL",
  verbose: 0,
  headless: process.env.STAGEHAND_UI_HEADLESS !== "false",
  localBrowserLaunchOptions: {
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-gpu",
      "--disable-dev-shm-usage",
    ],
  },
});

async function run() {
  try {
    await stagehand.init();
    const page = stagehand.page;
    await page.goto(targetUrl, { waitUntil: "load", timeout: 15000 });
    await page.waitForSelector(selector, { timeout: 10000 });
    console.log(`Stagehand QA passed: selector '${selector}' is present on ${targetUrl}.`);
  } finally {
    await stagehand.close().catch(() => {});
  }
}

run().catch((error) => {
  console.error("Stagehand QA runner failed:", error);
  process.exit(1);
});
