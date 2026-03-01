import { expect, test, type Page } from "@playwright/test";

const mockSearchResponse = {
  query: {
    postcode: "SW1A 1AA",
    radius_miles: 5
  },
  center: {
    lat: 51.501009,
    lng: -0.141588
  },
  count: 2,
  schools: [
    {
      urn: "100001",
      name: "Camden Bridge Primary School",
      type: "Community school",
      phase: "Primary",
      postcode: "NW1 8NH",
      lat: 51.5424,
      lng: -0.1418,
      distance_miles: 0.52
    },
    {
      urn: "100002",
      name: "Alden Civic Academy",
      type: "Academy sponsor led",
      phase: "Secondary",
      postcode: "NW1 5TX",
      lat: 51.5357,
      lng: -0.1299,
      distance_miles: 1.12
    }
  ]
};

async function expectPrimaryControlsVisible(page: Page): Promise<void> {
  await expect(page.getByRole("heading", { name: "Civitas Schools Discovery" })).toBeVisible();
  await expect(page.getByLabel("Postcode")).toBeVisible();
  await expect(page.getByLabel("Search radius")).toBeVisible();
  await expect(page.getByRole("button", { name: "Search schools" })).toBeVisible();
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

test("desktop: postcode search renders list and keyboard-focusable markers", async ({ page }) => {
  await page.route("**/api/v1/schools**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockSearchResponse)
    });
  });

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/");
  await expectPrimaryControlsVisible(page);

  await page.getByLabel("Postcode").fill("SW1A 1AA");
  await page.getByRole("button", { name: "Search schools" }).click();

  await expect(page.getByText("Camden Bridge Primary School")).toBeVisible();
  await expect(page.getByText("Alden Civic Academy")).toBeVisible();
  await expect(page.getByText("2 markers")).toBeVisible();

  const marker = page.locator('.leaflet-interactive[role="button"]').first();
  await expect(marker).toBeVisible();
  await marker.focus();
  await marker.press("Enter");

  await expect(page.getByText(/mi from search center/).first()).toBeVisible();
});

test("mobile: controls remain visible with map below list and touch targets sized", async ({ page }) => {
  await page.route("**/api/v1/schools**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockSearchResponse)
    });
  });

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

  await page.getByRole("button", { name: "Search schools" }).click();
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

