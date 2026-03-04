import { gzipSync } from "node:zlib";
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

const DIST_ASSETS = path.resolve("dist", "assets");

const BUDGETS_BYTES = {
  appShellJs: 170 * 1024,
  appShellCss: 35 * 1024,
  mapChunkJs: 300 * 1024
};

function toGzipSize(filePath) {
  const fileContents = readFileSync(filePath);
  return gzipSync(fileContents).byteLength;
}

function formatKiB(bytes) {
  return `${(bytes / 1024).toFixed(1)} KiB`;
}

function collectAssetFiles() {
  return readdirSync(DIST_ASSETS)
    .map((entry) => path.join(DIST_ASSETS, entry))
    .filter((entry) => statSync(entry).isFile());
}

function sumSizes(filePaths) {
  return filePaths.reduce((total, filePath) => total + toGzipSize(filePath), 0);
}

function isMapChunk(filePath) {
  const fileName = path.basename(filePath);
  return /map|leaflet|react-leaflet/i.test(fileName) && fileName.endsWith(".js");
}

function run() {
  const assets = collectAssetFiles();
  const cssAssets = assets.filter((asset) => asset.endsWith(".css"));
  const mapJsAssets = assets.filter(isMapChunk);
  const appJsAssets = assets.filter((asset) => asset.endsWith(".js") && !isMapChunk(asset));

  const appShellJsSize = sumSizes(appJsAssets);
  const appShellCssSize = sumSizes(cssAssets);
  const mapChunkJsSize = sumSizes(mapJsAssets);

  const checks = [
    {
      label: "App shell JS (gzip)",
      actual: appShellJsSize,
      budget: BUDGETS_BYTES.appShellJs
    },
    {
      label: "App shell CSS (gzip)",
      actual: appShellCssSize,
      budget: BUDGETS_BYTES.appShellCss
    },
    {
      label: "Lazy map chunk JS (gzip)",
      actual: mapChunkJsSize,
      budget: BUDGETS_BYTES.mapChunkJs
    }
  ];

  let failed = false;
  for (const check of checks) {
    const status = check.actual <= check.budget ? "PASS" : "FAIL";
    if (status === "FAIL") {
      failed = true;
    }
    console.log(
      `${status} ${check.label}: ${formatKiB(check.actual)} (budget ${formatKiB(check.budget)})`
    );
  }

  if (mapJsAssets.length === 0) {
    failed = true;
    console.error(
      "FAIL Lazy map chunk JS (gzip): no map chunk found. Ensure Leaflet is lazy-loaded via dynamic import."
    );
  }

  if (failed) {
    process.exitCode = 1;
  }
}

run();
