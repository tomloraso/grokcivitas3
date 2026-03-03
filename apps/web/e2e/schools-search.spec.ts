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

const mockProfileResponse = {
  school: {
    urn: "100001",
    name: "Camden Bridge Primary School",
    phase: "Primary",
    type: "Community school",
    status: "Open",
    postcode: "NW1 8NH",
    lat: 51.5424,
    lng: -0.1418
  },
  demographics_latest: {
    academic_year: "2024/25",
    disadvantaged_pct: 17.2,
    fsm_pct: null,
    sen_pct: 13.0,
    ehcp_pct: 2.1,
    eal_pct: 8.4,
    first_language_english_pct: 90.6,
    first_language_unclassified_pct: 1.0,
    coverage: {
      fsm_supported: false,
      ethnicity_supported: false,
      top_languages_supported: false
    }
  },
  ofsted_latest: {
    overall_effectiveness_code: "2",
    overall_effectiveness_label: "Good",
    inspection_start_date: "2025-10-10",
    publication_date: "2025-11-15",
    is_graded: true,
    ungraded_outcome: null
  },
  ofsted_timeline: {
    events: [
      {
        inspection_number: "10426709",
        inspection_start_date: "2025-11-11",
        publication_date: "2026-01-11",
        inspection_type: "Section 8",
        overall_effectiveness_label: null,
        headline_outcome_text: "Strong standard",
        category_of_concern: null
      }
    ],
    coverage: {
      is_partial_history: false,
      earliest_event_date: "2015-09-14",
      latest_event_date: "2026-01-15",
      events_count: 9
    }
  },
  area_context: {
    deprivation: {
      lsoa_code: "E01004736",
      imd_decile: 3,
      idaci_score: 0.241,
      idaci_decile: 2,
      source_release: "IoD2025"
    },
    crime: {
      radius_miles: 1,
      latest_month: "2026-01",
      total_incidents: 486,
      categories: [{ category: "violent-crime", incident_count: 132 }]
    },
    coverage: {
      has_deprivation: true,
      has_crime: true,
      crime_months_available: 12
    }
  }
};

const mockTrendsResponse = {
  urn: "100001",
  years_available: ["2024/25"],
  history_quality: { is_partial_history: true, min_years_for_delta: 2, years_count: 1 },
  series: {
    disadvantaged_pct: [
      { academic_year: "2024/25", value: 17.2, delta: null, direction: null }
    ],
    sen_pct: [],
    ehcp_pct: [],
    eal_pct: []
  }
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
  await expect(page.getByRole("region", { name: "Map view" })).toBeVisible();
  await expect(page.locator(".maplibregl-ctrl-zoom-in")).toBeVisible();
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
  const zoomIn = page.locator(".maplibregl-ctrl-zoom-in");
  await expect(zoomIn).toBeVisible();

  const zoomBox = await zoomIn.boundingBox();
  expect(zoomBox).not.toBeNull();
  if (!zoomBox) {
    return;
  }

  expect(zoomBox.width).toBeGreaterThanOrEqual(44);
  expect(zoomBox.height).toBeGreaterThanOrEqual(44);
});

test("search page shows header and suppresses footer for map-first layout", async ({ page }) => {
  await gotoRoute(page, "/");
  await expect(page.getByRole("banner")).toBeVisible();
  await expect(page.getByRole("contentinfo")).toHaveCount(0);
  await expect(page.getByLabel("Civitas - return to home")).toBeVisible();
});

test("click result navigates to school profile route", async ({ page }) => {
  await page.route("**/api/v1/schools?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockSearchResponse)
    });
  });
  await page.route("**/api/v1/schools/100001", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockProfileResponse)
    });
  });
  await page.route("**/api/v1/schools/100001/trends", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockTrendsResponse)
    });
  });

  await gotoRoute(page, "/");
  await page.getByLabel("Postcode").fill("SW1A 1AA");
  await page.getByRole("button", { name: "Search schools" }).click();
  await expect(page.getByText("Camden Bridge Primary School")).toBeVisible();

  await page.getByLabel("View profile for Camden Bridge Primary School").click();
  await expect(page).toHaveURL(/\/schools\/100001$/);
  await expect(page.getByRole("heading", { name: "Camden Bridge Primary School" })).toBeVisible();
  await expect(page.getByText("Demographics")).toBeVisible();
  await expect(page.getByLabel(/Ofsted rating: Good/)).toBeVisible();
  await expect(page.getByText("Ofsted Timeline")).toBeVisible();
  await expect(page.getByText("Area Deprivation")).toBeVisible();
  await expect(page.getByText("Area Crime")).toBeVisible();
});

test("browser back returns to search from school profile", async ({ page }) => {
  await page.route("**/api/v1/schools/100001", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockProfileResponse)
    });
  });
  await page.route("**/api/v1/schools/100001/trends", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockTrendsResponse)
    });
  });

  await gotoRoute(page, "/");
  await gotoRoute(page, "/schools/100001");
  await page.goBack();

  await expect(page).toHaveURL("/");
  await expect(page.getByRole("heading", { name: "Find schools near you" })).toBeVisible();
});

test("header Search link navigates back to search route", async ({ page }) => {
  await page.route("**/api/v1/schools/100001", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockProfileResponse)
    });
  });
  await page.route("**/api/v1/schools/100001/trends", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockTrendsResponse)
    });
  });

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

test("desktop: collapse toggle reduces panel and expand restores it", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await gotoRoute(page, "/");
  await expectPrimaryControlsVisible(page);

  const panel = page.getByRole("region", { name: "Results panel" });
  const expandedBox = await panel.boundingBox();
  expect(expandedBox).not.toBeNull();

  // Collapse the panel
  await page.getByRole("button", { name: "Collapse results panel" }).click();
  const collapsedBox = await panel.boundingBox();
  expect(collapsedBox).not.toBeNull();

  if (expandedBox && collapsedBox) {
    expect(collapsedBox.width).toBeLessThan(expandedBox.width);
  }

  // Expand again
  await page.getByRole("button", { name: "Expand results panel" }).click();
  const restoredBox = await panel.boundingBox();
  expect(restoredBox).not.toBeNull();

  if (expandedBox && restoredBox) {
    expect(restoredBox.width).toBeCloseTo(expandedBox.width, -1);
  }
});

test("mobile: bottom-sheet expands and collapses while map stays visible", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await gotoRoute(page, "/");

  const mapSection = page.getByRole("region", { name: "Map view" });
  const panel = page.getByRole("region", { name: "Results panel" });
  await expect(mapSection).toBeVisible();
  await expect(panel).toBeVisible();

  // Expand the sheet
  await page.getByRole("button", { name: "Expand results panel" }).click();
  await expect(page.getByRole("button", { name: "Collapse results panel" })).toBeVisible();

  // Map should still be visible (behind the sheet)
  await expect(mapSection).toBeVisible();

  // Collapse the sheet
  await page.getByRole("button", { name: "Collapse results panel" }).click();
  await expect(page.getByRole("button", { name: "Expand results panel" })).toBeVisible();
});

test("desktop: keyboard navigation remains functional with scrollbar-hide", async ({ page }) => {
  await page.route("**/api/v1/schools**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockSearchResponse)
    });
  });

  await page.setViewportSize({ width: 1280, height: 900 });
  await gotoRoute(page, "/");
  await page.getByLabel("Postcode").fill("SW1A 1AA");
  await page.getByRole("button", { name: "Search schools" }).click();
  await expect(page.getByText("Camden Bridge Primary School")).toBeVisible();

  // Tab through results — focus should reach result links
  await page.keyboard.press("Tab");
  const focused = page.locator(":focus");
  await expect(focused).toBeVisible();
});
