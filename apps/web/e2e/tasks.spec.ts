import { expect, test, type Page } from "@playwright/test";

async function expectPrimaryControlsVisible(page: Page): Promise<void> {
  await expect(page.getByRole("heading", { name: "Civitas Schools Discovery" })).toBeVisible();
  await expect(page.getByLabel("Postcode")).toBeVisible();
  await expect(page.getByLabel("Search radius")).toBeVisible();
  await expect(page.getByLabel("Preview state")).toBeVisible();
  await expect(page.getByRole("button", { name: "Search schools" })).toBeVisible();
}

async function selectPreviewState(page: Page, option: "Results" | "Loading" | "Empty" | "Error"): Promise<void> {
  await page.getByLabel("Preview state").click();
  await page.getByRole("option", { name: option }).click();
}

test("desktop: split pane keeps list and map side by side", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/");
  await expectPrimaryControlsVisible(page);

  const listSection = page.getByLabel("School results");
  const mapSection = page.getByLabel("Map view");
  await expect(listSection).toBeVisible();
  await expect(mapSection).toBeVisible();

  const listBox = await listSection.boundingBox();
  const mapBox = await mapSection.boundingBox();
  expect(listBox).not.toBeNull();
  expect(mapBox).not.toBeNull();

  if (!listBox || !mapBox) {
    return;
  }

  expect(mapBox.x).toBeGreaterThan(listBox.x);
  expect(Math.abs(mapBox.y - listBox.y)).toBeLessThan(120);
});

test("tablet: layout stacks without hiding controls", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto("/");
  await expectPrimaryControlsVisible(page);

  const listSection = page.getByLabel("School results");
  const mapSection = page.getByLabel("Map view");
  const listBox = await listSection.boundingBox();
  const mapBox = await mapSection.boundingBox();
  expect(listBox).not.toBeNull();
  expect(mapBox).not.toBeNull();

  if (!listBox || !mapBox) {
    return;
  }

  expect(mapBox.y).toBeGreaterThan(listBox.y + listBox.height - 1);
});

test("desktop: map markers support keyboard popup interaction", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/");
  await expectPrimaryControlsVisible(page);
  await selectPreviewState(page, "Results");

  const marker = page.locator('.leaflet-interactive[role="button"]').first();
  await expect(marker).toBeVisible();
  await marker.focus();
  await marker.press("Enter");

  await expect(page.getByText(/mi from search center/).first()).toBeVisible();
});

test("mobile: controls remain visible with map below list and touch targets sized", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expectPrimaryControlsVisible(page);

  const listSection = page.getByLabel("School results");
  const mapSection = page.getByLabel("Map view");
  const listBox = await listSection.boundingBox();
  const mapBox = await mapSection.boundingBox();
  expect(listBox).not.toBeNull();
  expect(mapBox).not.toBeNull();

  if (!listBox || !mapBox) {
    return;
  }

  expect(mapBox.y).toBeGreaterThan(listBox.y + listBox.height - 1);

  await selectPreviewState(page, "Results");
  const zoomIn = page.locator(".leaflet-control-zoom-in");
  await expect(zoomIn).toBeVisible();

  const zoomBox = await zoomIn.boundingBox();
  expect(zoomBox).not.toBeNull();
  if (!zoomBox) {
    return;
  }

  expect(zoomBox.width).toBeGreaterThanOrEqual(44);
  expect(zoomBox.height).toBeGreaterThanOrEqual(44);
});

