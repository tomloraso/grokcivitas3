import { expect, test, type Page } from "@playwright/test";

import { COMPARE_RESPONSE } from "../src/features/school-compare/testData";
import {
  DASHBOARD_RESPONSE,
  PROFILE_RESPONSE,
  TRENDS_RESPONSE
} from "../src/features/school-profile/testData";

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
      name: "Primary Example",
      type: "Community school",
      phase: "Primary",
      postcode: "SW1A 1AA",
      lat: 51.5424,
      lng: -0.1418,
      distance_miles: 0.52
    },
    {
      urn: "200002",
      name: "Secondary Example",
      type: "Academy sponsor led",
      phase: "Secondary",
      postcode: "SW1A 2BB",
      lat: 51.5357,
      lng: -0.1299,
      distance_miles: 1.12
    }
  ]
};

async function gotoRoute(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: "domcontentloaded" });
}

function buildProfileResponse(overrides: {
  urn: string;
  name: string;
  phase: string;
  type: string;
  postcode: string;
  lowAge: number;
  highAge: number;
}) {
  const response = structuredClone(PROFILE_RESPONSE);
  response.school.urn = overrides.urn;
  response.school.name = overrides.name;
  response.school.phase = overrides.phase;
  response.school.type = overrides.type;
  response.school.postcode = overrides.postcode;
  response.school.statutory_low_age = overrides.lowAge;
  response.school.statutory_high_age = overrides.highAge;
  return response;
}

function buildTrendsResponse(urn: string) {
  const response = structuredClone(TRENDS_RESPONSE);
  response.urn = urn;
  return response;
}

function buildDashboardResponse() {
  return structuredClone(DASHBOARD_RESPONSE);
}

async function registerCompareRoutes(page: Page): Promise<void> {
  const profiles = {
    "100001": buildProfileResponse({
      urn: "100001",
      name: "Primary Example",
      phase: "Primary",
      type: "Community school",
      postcode: "SW1A 1AA",
      lowAge: 4,
      highAge: 11
    }),
    "200002": buildProfileResponse({
      urn: "200002",
      name: "Secondary Example",
      phase: "Secondary",
      type: "Academy sponsor led",
      postcode: "SW1A 2BB",
      lowAge: 11,
      highAge: 18
    })
  } as const;

  await page.route("**/api/v1/schools?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockSearchResponse)
    });
  });

  await page.route("**/api/v1/schools/compare?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(COMPARE_RESPONSE)
    });
  });

  for (const [urn, profile] of Object.entries(profiles)) {
    await page.route(`**/api/v1/schools/${urn}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(profile)
      });
    });

    await page.route(`**/api/v1/schools/${urn}/trends`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildTrendsResponse(urn))
      });
    });

    await page.route(`**/api/v1/schools/${urn}/trends/dashboard`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildDashboardResponse())
      });
    });
  }
}

test("search entry builds a compare set and keeps compare context on profile navigation", async ({
  page
}) => {
  await registerCompareRoutes(page);

  await gotoRoute(page, "/");
  await page.getByLabel("Search*").fill("SW1A 1AA");
  await page.getByRole("button", { name: "Search schools" }).click();

  await expect(page.getByText("Primary Example")).toBeVisible();
  await expect(page.getByText("Secondary Example")).toBeVisible();

  await page.getByRole("button", { name: "Add to compare" }).first().click();
  await page.getByRole("button", { name: "Add to compare" }).first().click();

  await page.getByRole("link", { name: /Compare 2\/4 selected/ }).click();

  await expect(
    page.getByRole("heading", { name: "Compare schools side by side" })
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Demographics" })).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Primary Example", exact: true })
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Secondary Example", exact: true })
  ).toBeVisible();

  await page
    .locator("a", { hasText: "Primary Example" })
    .first()
    .click();

  await expect(page).toHaveURL(/\/schools\/100001$/);
  await expect(page.getByRole("heading", { name: "Primary Example" })).toBeVisible();
  await expect(
    page
      .getByRole("navigation", { name: "Breadcrumb" })
      .getByRole("link", { name: "Compare", exact: true })
  ).toBeVisible();
});

test("compare remove action lands in the underfilled state", async ({ page }) => {
  await registerCompareRoutes(page);

  await gotoRoute(page, "/compare?urns=100001,200002");

  await expect(page.getByRole("heading", { name: "Selected schools" })).toBeVisible();
  await page.getByRole("button", { name: "Remove" }).first().click();

  await expect(page).toHaveURL(/\/compare\?urns=200002$/);
  await expect(
    page.getByRole("heading", { name: "Add one more school to compare" })
  ).toBeVisible();
  await expect(page.getByText("Secondary Example")).toBeVisible();
});

test("profile entry points can build and open compare", async ({ page }) => {
  await registerCompareRoutes(page);

  await gotoRoute(page, "/schools/100001");
  await page.getByRole("button", { name: "Add to compare" }).click();
  await page.waitForFunction(
    () =>
      window.localStorage
        .getItem("civitas.compare.selection")
        ?.includes('"urn":"100001"') ?? false
  );

  await gotoRoute(page, "/schools/200002");
  await page.getByRole("button", { name: "Add to compare" }).click();
  await page.getByRole("link", { name: /Compare 2\/4 selected/ }).click();

  await expect(
    page.getByRole("heading", { name: "Compare schools side by side" })
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Inspection" })).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Primary Example", exact: true })
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Secondary Example", exact: true })
  ).toBeVisible();
});

test("explicit empty compare URL does not revive stored compare selection", async ({
  page
}) => {
  await registerCompareRoutes(page);
  await page.addInitScript((storedSelection) => {
    window.localStorage.setItem(
      "civitas.compare.selection",
      JSON.stringify(storedSelection)
    );
  }, [
    {
      urn: "100001",
      name: "Primary Example",
      phase: "Primary",
      type: "Community school",
      postcode: "SW1A 1AA",
      source: "search"
    },
    {
      urn: "200002",
      name: "Secondary Example",
      phase: "Secondary",
      type: "Academy sponsor led",
      postcode: "SW1A 2BB",
      source: "search"
    }
  ]);

  await gotoRoute(page, "/compare?urns=");

  await expect(
    page.getByRole("heading", { name: "Start a compare set" })
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Compare 0/4 selected" })
  ).toBeDisabled();
});

test("compare matrix remains horizontally scrollable on small viewports", async ({
  page
}) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await registerCompareRoutes(page);

  await gotoRoute(page, "/compare?urns=100001,200002");

  await expect(
    page.getByRole("heading", { name: "Compare schools side by side" })
  ).toBeVisible();

  const matrixScrollMetrics = await page
    .getByRole("table", { name: "Demographics comparison table" })
    .evaluate((table) => {
      const container = table.parentElement as HTMLElement | null;
      if (!container) {
        return { clientWidth: 0, scrollWidth: 0 };
      }
      return {
        clientWidth: container.clientWidth,
        scrollWidth: container.scrollWidth
      };
    });

  expect(matrixScrollMetrics.scrollWidth).toBeGreaterThan(
    matrixScrollMetrics.clientWidth
  );
});
