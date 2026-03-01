import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { chromium } from "@playwright/test";

const HOST = "127.0.0.1";
const PREVIEW_PORT = Number(
  process.env.LIGHTHOUSE_PREVIEW_PORT ?? String(4300 + Math.floor(Math.random() * 200))
);
const TARGET_URL = `http://${HOST}:${PREVIEW_PORT}/`;
const ARTIFACT_DIR = path.resolve("artifacts", "lighthouse");
const VITE_CLI = path.resolve("node_modules", "vite", "bin", "vite.js");
const LIGHTHOUSE_CLI = path.resolve("node_modules", "lighthouse", "cli", "index.js");

const THRESHOLDS = {
  lcpMs: 2000,
  cls: 0.1,
  tbtMs: 200
};

function startPreviewServer() {
  return spawn(
    process.execPath,
    [VITE_CLI, "preview", "--host", HOST, "--port", String(PREVIEW_PORT), "--strictPort"],
    {
      shell: false,
      stdio: "pipe"
    }
  );
}

function runLighthouse(url, chromePath) {
  const profileDir = mkdtempSync(path.join(tmpdir(), "civitas-lighthouse-"));
  const chromeFlags = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    `--user-data-dir=${profileDir}`
  ].join(" ");

  const args = [
    LIGHTHOUSE_CLI,
    url,
    `--chrome-path=${chromePath}`,
    "--quiet",
    `--chrome-flags=${chromeFlags}`,
    "--only-categories=performance",
    "--emulated-form-factor=mobile",
    "--output=json",
    "--output-path=stdout"
  ];

  return new Promise((resolve, reject) => {
    const processRef = spawn(process.execPath, args, {
      shell: false,
      stdio: "pipe",
      env: {
        ...process.env,
        CHROME_PATH: chromePath
      }
    });

    let stdout = "";
    let stderr = "";
    const timeoutRef = setTimeout(() => {
      processRef.kill("SIGTERM");
      reject(new Error("Lighthouse timed out after 180s"));
    }, 180_000);

    processRef.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    processRef.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    processRef.on("error", (error) => {
      clearTimeout(timeoutRef);
      reject(error);
    });

    processRef.on("close", (code) => {
      clearTimeout(timeoutRef);
      if (code !== 0) {
        reject(new Error(stderr.trim() || `Lighthouse exited with code ${code}`));
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`Failed to parse Lighthouse output: ${String(error)}`));
      }
    });
  });
}

async function runLighthouseWithRetry(url, chromePath, retries = 2) {
  for (let attempt = 1; attempt <= retries; attempt += 1) {
    try {
      return await runLighthouse(url, chromePath);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (!message.includes("EBUSY") || attempt === retries) {
        throw error;
      }
      await delay(1500);
    }
  }
  throw new Error("Unreachable Lighthouse retry path");
}

async function waitForPreview(url) {
  const attempts = 60;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
    } catch {
      // Ignore while server is starting.
    }
    await delay(500);
  }
  throw new Error(`Preview server did not become ready at ${url}`);
}

function readMetric(lhr, auditId) {
  const metric = lhr.audits[auditId]?.numericValue;
  if (typeof metric !== "number") {
    throw new Error(`Missing Lighthouse metric: ${auditId}`);
  }
  return metric;
}

function formatMs(value) {
  return `${value.toFixed(0)}ms`;
}

function formatCls(value) {
  return value.toFixed(3);
}

function stopProcess(processRef) {
  if (!processRef || processRef.killed) {
    return;
  }
  processRef.kill("SIGTERM");
}

async function run() {
  let previewServer;

  try {
    const chromePath = chromium.executablePath();
    if (!existsSync(chromePath)) {
      throw new Error(
        "Playwright Chromium is not installed. Run: cd apps/web && npx playwright install chromium"
      );
    }

    previewServer = startPreviewServer();
    previewServer.stdout.on("data", (chunk) => {
      const text = chunk.toString();
      if (text.includes("Local")) {
        process.stdout.write(text);
      }
    });
    previewServer.stderr.on("data", (chunk) => {
      process.stderr.write(chunk);
    });

    console.log(`Starting preview server at ${TARGET_URL}`);
    await waitForPreview(TARGET_URL);
    console.log("Running Lighthouse mobile performance audit");
    const lhr = await runLighthouseWithRetry(TARGET_URL, chromePath);

    const metrics = {
      lcpMs: readMetric(lhr, "largest-contentful-paint"),
      cls: readMetric(lhr, "cumulative-layout-shift"),
      tbtMs: readMetric(lhr, "total-blocking-time")
    };

    const checks = [
      {
        label: "LCP",
        actual: metrics.lcpMs,
        budget: THRESHOLDS.lcpMs,
        format: formatMs
      },
      {
        label: "CLS",
        actual: metrics.cls,
        budget: THRESHOLDS.cls,
        format: formatCls
      },
      {
        label: "TBT",
        actual: metrics.tbtMs,
        budget: THRESHOLDS.tbtMs,
        format: formatMs
      }
    ];

    let failed = false;
    for (const check of checks) {
      const status = check.actual <= check.budget ? "PASS" : "FAIL";
      if (status === "FAIL") {
        failed = true;
      }
      console.log(
        `${status} ${check.label}: ${check.format(check.actual)} (budget ${check.format(check.budget)})`
      );
    }

    mkdirSync(ARTIFACT_DIR, { recursive: true });
    const snapshot = {
      capturedAt: new Date().toISOString(),
      targetUrl: TARGET_URL,
      lighthouseVersion: lhr.lighthouseVersion,
      performanceScore: lhr.categories.performance.score,
      thresholds: THRESHOLDS,
      metrics
    };

    writeFileSync(path.join(ARTIFACT_DIR, "latest.json"), JSON.stringify(snapshot, null, 2));

    if (failed) {
      process.exitCode = 1;
    }
  } finally {
    stopProcess(previewServer);
  }
}

run().catch((error) => {
  console.error(`FAIL Lighthouse check: ${error.message}`);
  process.exitCode = 1;
});
