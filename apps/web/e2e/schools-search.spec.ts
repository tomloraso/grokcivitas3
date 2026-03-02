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
  await expect(page.getByRole("heading", { name: "Find schools near you" })).toBeVisible();
  await expect(page.getByLabel("Postcode")).toBeVisible();
  await expect(page.getByLabel("Search radius")).toBeVisible();
  await expect(page.getByRole("button", { name: "Search schools" })).toBeVisible();
}

async function gotoRoute(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: "domcontentloaded" });
}

test("desktop: map overlay layout renders map canvas with floating panel", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await gotoRoute(page, "/");
  await expectPrimaryControlsVisible(page);

  const overlayRoot = page.locator('[data-layout="map-overlay"]');
  const mapSection = page.getByRole("region", { name: "Map view" });
  const resultsSection = page.getByLabel("School results");

  await expect(overlayRoot).toBeVisible();
  await expect(mapSection).toBeVisible();
  await expect(resultsSection).toBeVisible();

  const mapBox = await mapSection.boundingBox();
  const resultsBox = await resultsSection.boundingBox();
  expect(mapBox).not.toBeNull();
  expect(resultsBox).not.toBeNull();

  if (!mapBox || !resultsBox) {
    return;
  }

  expect(mapBox.width).toBeGreaterThan(resultsBox.width);
  expect(resultsBox.x).toBeLessThan(mapBox.width / 2);
});

test("mobile: overlay keeps controls visible and scrollable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await gotoRoute(page, "/");
  await expectPrimaryControlsVisible(page);

  const overlayRoot = page.locator('[data-layout="map-overlay"]');
  const resultsSection = page.getByLabel("School results");
  await expect(overlayRoot).toBeVisible();
  await expect(resultsSection).toBeVisible();

  const overlayBox = await overlayRoot.boundingBox();
  const resultsBox = await resultsSection.boundingBox();
  expect(overlayBox).not.toBeNull();
  expect(resultsBox).not.toBeNull();

  if (!overlayBox || !resultsBox) {
    return;
  }

  expect(resultsBox.width).toBeLessThanOrEqual(overlayBox.width);
  expect(resultsBox.height).toBeGreaterThan(0);
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
  await gotoRoute(page, "/");
  await expectPrimaryControlsVisible(page);

  await page.getByLabel("Postcode").fill("SW1A 1AA");
  await page.getByRole("button", { name: "Search schools" }).click();

  await expect(page.getByText("Camden Bridge Primary School")).toBeVisible();
  await expect(page.getByText("Alden Civic Academy")).toBeVisible();

  const marker = page.locator('.leaflet-interactive[role="button"]').first();
  await expect(marker).toBeVisible();
  await marker.focus();
  await marker.press("Enter");

  await expect(page.getByText(/mi from search center/).first()).toBeVisible();
});

test("mobile: map zoom controls retain touch target size", async ({ page }) => {
  await page.route("**/api/v1/schools**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockSearchResponse)
    });
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await gotoRoute(page, "/");
  await expectPrimaryControlsVisible(page);

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

test("site header and footer are visible on the search page", async ({ page }) => {
  await gotoRoute(page, "/");
  await expect(page.getByRole("banner")).toBeVisible();
  await expect(page.getByRole("contentinfo")).toBeVisible();
  await expect(page.getByLabel("Civitas - return to home")).toBeVisible();
});

test("click result navigates to school profile route", async ({ page }) => {
  await page.route("**/api/v1/schools**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockSearchResponse)
    });
  });

  await gotoRoute(page, "/");
  await page.getByLabel("Postcode").fill("SW1A 1AA");
  await page.getByRole("button", { name: "Search schools" }).click();
  await expect(page.getByText("Camden Bridge Primary School")).toBeVisible();

  await page.getByLabel("View profile for Camden Bridge Primary School").click();
  await expect(page).toHaveURL(/\/schools\/100001$/);
  await expect(page.getByRole("heading", { name: /100001/ })).toBeVisible();
});

test("browser back returns to search from school profile", async ({ page }) => {
  await gotoRoute(page, "/");
  await gotoRoute(page, "/schools/100001");
  await page.goBack();

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Find schools near you" })).toBeVisible();
});

test("header Search link navigates back to search route", async ({ page }) => {
  await gotoRoute(page, "/schools/100001");
  await page.getByRole("banner").getByRole("link", { name: "Search", exact: true }).click();
  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Find schools near you" })).toBeVisible();
});

test("unknown route renders not-found page", async ({ page }) => {
  await gotoRoute(page, "/does-not-exist");
  await expect(page.getByRole("heading", { name: "Page not found" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Back to search" })).toBeVisible();
});
