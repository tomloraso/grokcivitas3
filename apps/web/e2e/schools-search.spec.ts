import { expect, test, type Page } from "@playwright/test";

import {
  DASHBOARD_RESPONSE,
  PROFILE_RESPONSE,
  TRENDS_RESPONSE,
} from "../src/features/school-profile/testData";

const PRODUCT_CODE = "premium_launch";

const mockSearchResponse = {
  query: {
    postcode: "SW1A 1AA",
    radius_miles: 5,
    phases: ["primary", "secondary"],
    sort: "closest",
  },
  center: {
    lat: 51.501009,
    lng: -0.141588,
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
      distance_miles: 0.52,
      pupil_count: 420,
      latest_ofsted: {
        label: "Good",
        sort_rank: 2,
        availability: "published",
      },
      academic_metric: {
        metric_key: "ks2_combined_expected_pct",
        label: "KS2 expected standard",
        display_value: "67%",
        sort_value: 67,
        availability: "published",
      },
    },
    {
      urn: "100002",
      name: "Alden Civic Academy",
      type: "Academy sponsor led",
      phase: "Secondary",
      postcode: "NW1 5TX",
      lat: 51.5357,
      lng: -0.1299,
      distance_miles: 1.12,
      pupil_count: 780,
      latest_ofsted: {
        label: "Outstanding",
        sort_rank: 1,
        availability: "published",
      },
      academic_metric: {
        metric_key: "progress8_average",
        label: "Progress 8",
        display_value: "+0.18",
        sort_value: 0.18,
        availability: "published",
      },
    },
  ],
};

function clone<T>(value: T): T {
  return structuredClone(value);
}

function buildProfileResponse() {
  const response = clone(PROFILE_RESPONSE);
  response.school.urn = "100001";
  response.school.name = "Camden Bridge Primary School";
  response.school.phase = "Primary";
  response.school.type = "Community school";
  response.school.postcode = "NW1 8NH";
  response.analyst = {
    access: {
      state: "locked",
      capability_key: "premium_ai_analyst",
      reason_code: "anonymous_user",
      product_codes: [PRODUCT_CODE],
      requires_auth: true,
      requires_purchase: false,
      school_name: response.school.name,
    },
    text: null,
    teaser_text:
      "Preview the first evidence-grounded analyst signals before unlocking the full Premium narrative.",
    disclaimer:
      "This analyst view is AI-generated from public government data. It highlights patterns in the published evidence, but it is not official advice or a recommendation.",
  };
  response.neighbourhood = {
    access: {
      state: "locked",
      capability_key: "premium_neighbourhood",
      reason_code: "anonymous_user",
      product_codes: [PRODUCT_CODE],
      requires_auth: true,
      requires_purchase: false,
      school_name: response.school.name,
    },
    area_context: null,
    teaser_text:
      "Premium neighbourhood context is available for this school, including deprivation context, local crime context, and house-price context.",
  };
  return response;
}

function buildTrendsResponse() {
  const response = clone(TRENDS_RESPONSE);
  response.urn = "100001";
  return response;
}

function buildDashboardResponse() {
  const response = clone(DASHBOARD_RESPONSE);
  response.urn = "100001";
  return response;
}

function searchInput(page: Page) {
  return page.getByRole("textbox", { name: "Search" });
}

async function expectPrimaryControlsVisible(page: Page): Promise<void> {
  await expect(page.getByRole("heading", { name: "Find schools near you" })).toBeVisible();
  await expect(searchInput(page)).toBeVisible();
  await expect(page.getByRole("button", { name: "Search schools" })).toBeVisible();
}

async function gotoRoute(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: "domcontentloaded" });
}

async function registerSearchResultsRoute(page: Page): Promise<void> {
  await page.route("**/api/v1/schools?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockSearchResponse),
    });
  });
}

async function registerProfileRoutes(page: Page): Promise<void> {
  await page.route("**/api/v1/schools/100001", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildProfileResponse()),
    });
  });
  await page.route("**/api/v1/schools/100001/trends", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildTrendsResponse()),
    });
  });
  await page.route("**/api/v1/schools/100001/trends/dashboard", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildDashboardResponse()),
    });
  });
}

test("desktop: map overlay layout renders map canvas with floating panel", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await gotoRoute(page, "/");
  await expectPrimaryControlsVisible(page);

  const overlayRoot = page.locator('[data-layout="map-overlay"]');
  const mapSection = page.getByRole("region", { name: "Map view" });
  const panel = page.getByRole("region", { name: "Results panel" });

  await expect(overlayRoot).toBeVisible();
  await expect(mapSection).toBeVisible();
  await expect(panel).toBeVisible();

  const mapBox = await mapSection.boundingBox();
  const panelBox = await panel.boundingBox();
  expect(mapBox).not.toBeNull();
  expect(panelBox).not.toBeNull();

  if (!mapBox || !panelBox) {
    return;
  }

  expect(mapBox.width).toBeGreaterThan(panelBox.width);
  expect(panelBox.x).toBeLessThan(mapBox.width / 2);
});

test("mobile: overlay keeps controls visible and scrollable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await gotoRoute(page, "/");
  await expectPrimaryControlsVisible(page);

  const overlayRoot = page.locator('[data-layout="map-overlay"]');
  const panel = page.getByRole("region", { name: "Results panel" });
  await expect(overlayRoot).toBeVisible();
  await expect(panel).toBeVisible();

  const overlayBox = await overlayRoot.boundingBox();
  const panelBox = await panel.boundingBox();
  expect(overlayBox).not.toBeNull();
  expect(panelBox).not.toBeNull();

  if (!overlayBox || !panelBox) {
    return;
  }

  expect(panelBox.width).toBeLessThanOrEqual(overlayBox.width);
  expect(panelBox.height).toBeGreaterThan(0);
});

test("desktop: postcode search renders list and map context", async ({ page }) => {
  await registerSearchResultsRoute(page);

  await page.setViewportSize({ width: 1280, height: 900 });
  await gotoRoute(page, "/");
  await expectPrimaryControlsVisible(page);

  await searchInput(page).fill("SW1A 1AA");
  await expect(page.getByRole("combobox", { name: "Search radius" })).toBeVisible();
  await page.getByRole("button", { name: "Search schools" }).click();

  await expect(page.getByText("Camden Bridge Primary School")).toBeVisible();
  await expect(page.getByText("Alden Civic Academy")).toBeVisible();
  await expect(page.getByRole("region", { name: "Map view" })).toBeVisible();
  await expect(page.locator(".maplibregl-ctrl-zoom-in")).toBeVisible();
});

test("mobile: map zoom controls remain visible after postcode search", async ({ page }) => {
  await registerSearchResultsRoute(page);

  await page.setViewportSize({ width: 390, height: 844 });
  await gotoRoute(page, "/");
  await expectPrimaryControlsVisible(page);

  await searchInput(page).fill("SW1A 1AA");
  await expect(page.getByRole("combobox", { name: "Search radius" })).toBeVisible();
  await page.getByRole("button", { name: "Search schools" }).click();
  const zoomIn = page.locator(".maplibregl-ctrl-zoom-in");
  await expect(zoomIn).toBeVisible();

  const zoomBox = await zoomIn.boundingBox();
  expect(zoomBox).not.toBeNull();
  if (!zoomBox) {
    return;
  }

  expect(zoomBox.width).toBeGreaterThanOrEqual(28);
  expect(zoomBox.height).toBeGreaterThanOrEqual(28);
});

test("search page shows header and suppresses footer for map-first layout", async ({
  page,
}) => {
  await gotoRoute(page, "/");
  await expect(page.getByRole("banner")).toBeVisible();
  await expect(page.getByRole("contentinfo")).toHaveCount(0);
  await expect(page.getByLabel("Civitas - return to home")).toBeVisible();
});

test("click result navigates to school profile route with premium sections locked", async ({
  page,
}) => {
  await registerSearchResultsRoute(page);
  await registerProfileRoutes(page);

  await gotoRoute(page, "/");
  await searchInput(page).fill("SW1A 1AA");
  await expect(page.getByRole("combobox", { name: "Search radius" })).toBeVisible();
  await page.getByRole("button", { name: "Search schools" }).click();
  await expect(page.getByText("Camden Bridge Primary School")).toBeVisible();

  await page.getByLabel("View profile for Camden Bridge Primary School").click();
  await expect(page).toHaveURL(/\/schools\/100001$/);
  await expect(
    page.getByRole("heading", { name: "Camden Bridge Primary School", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Pupil Demographics")).toBeVisible();
  await expect(page.getByText("Ofsted Profile")).toBeVisible();
  await expect(page.getByText("Analyst Preview")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Neighbourhood Context", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Sign in to continue" }).first()).toBeVisible();
  await expect(page.getByText("Area Deprivation")).toHaveCount(0);
  await expect(page.getByText("Area Crime")).toHaveCount(0);
});

test("browser back returns to search from school profile", async ({ page }) => {
  await registerProfileRoutes(page);

  await gotoRoute(page, "/");
  await gotoRoute(page, "/schools/100001");
  await page.goBack();

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Find schools near you" })).toBeVisible();
});

test("header brand link navigates back to search route", async ({ page }) => {
  await registerProfileRoutes(page);

  await gotoRoute(page, "/schools/100001");
  await page.getByLabel("Civitas - return to home").click();
  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Find schools near you" })).toBeVisible();
});

test("unknown route renders not-found page", async ({ page }) => {
  await gotoRoute(page, "/does-not-exist");
  await expect(page.getByRole("heading", { name: "Page not found" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Back to search" })).toBeVisible();
});

test("desktop: results panel exposes the resize handle", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await gotoRoute(page, "/");
  await expectPrimaryControlsVisible(page);

  const resizeHandle = page.getByRole("separator", { name: /Resize panel/ });
  await expect(resizeHandle).toBeVisible();
  await expect(resizeHandle).toHaveAttribute("aria-valuemin", "280");
  await expect(resizeHandle).toHaveAttribute("aria-valuemax", "480");
});

test("mobile: bottom-sheet expands and collapses while map stays visible", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await gotoRoute(page, "/");

  const mapSection = page.getByRole("region", { name: "Map view" });
  const panel = page.getByRole("region", { name: "Results panel" });
  await expect(mapSection).toBeVisible();
  await expect(panel).toBeVisible();

  await page.getByRole("button", { name: "Expand results panel" }).click();
  await expect(page.getByRole("button", { name: "Collapse results panel" })).toBeVisible();
  await expect(mapSection).toBeVisible();

  await page.getByRole("button", { name: "Collapse results panel" }).click();
  await expect(page.getByRole("button", { name: "Expand results panel" })).toBeVisible();
});

test("desktop: keyboard navigation remains functional with scrollbar-hide", async ({
  page,
}) => {
  await registerSearchResultsRoute(page);

  await page.setViewportSize({ width: 1280, height: 900 });
  await gotoRoute(page, "/");
  await searchInput(page).fill("SW1A 1AA");
  await expect(page.getByRole("combobox", { name: "Search radius" })).toBeVisible();
  await page.getByRole("button", { name: "Search schools" }).click();
  await expect(page.getByText("Camden Bridge Primary School")).toBeVisible();

  await page.keyboard.press("Tab");
  const focused = page.locator(":focus");
  await expect(focused).toBeVisible();
});
