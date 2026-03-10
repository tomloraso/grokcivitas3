import { expect, test, type Page } from "@playwright/test"

import { COMPARE_RESPONSE } from "../src/features/school-compare/testData"
import {
  DASHBOARD_RESPONSE,
  PROFILE_RESPONSE,
  TRENDS_RESPONSE
} from "../src/features/school-profile/testData"

const USER_ID = "1a8538b9-3099-4ee6-b14b-e8cb4a7af5ca"
const USER_EMAIL = "person@example.com"
const CHECKOUT_ID = "0f4b5984-a6b1-47dd-a98d-6a6ab866d506"
const PRODUCT_CODE = "premium_launch"
const PREMIUM_CAPABILITIES = [
  "premium_ai_analyst",
  "premium_comparison",
  "premium_neighbourhood"
]

type AccessState = "anonymous" | "free" | "premium"

interface PremiumJourneyState {
  accessState: AccessState
  checkoutStatusPolls: number
  profileRequestCount: number
  compareRequestCount: number
}

function clone<T>(value: T): T {
  return structuredClone(value)
}

function buildSessionResponse(accessState: AccessState) {
  if (accessState === "anonymous") {
    return {
      state: "anonymous",
      user: null,
      expires_at: null,
      anonymous_reason: "missing",
      account_access_state: "anonymous",
      capability_keys: [],
      access_epoch: "anonymous:none"
    }
  }

  const capabilityKeys = accessState === "premium" ? PREMIUM_CAPABILITIES : []
  return {
    state: "authenticated",
    user: {
      id: USER_ID,
      email: USER_EMAIL
    },
    expires_at: "2026-03-21T10:00:00Z",
    anonymous_reason: null,
    account_access_state: accessState,
    capability_keys: capabilityKeys,
    access_epoch:
      capabilityKeys.length > 0
        ? `premium:${capabilityKeys.join(",")}`
        : "free:none"
  }
}

function buildAccountAccessResponse(accessState: AccessState) {
  const capabilityKeys = accessState === "premium" ? PREMIUM_CAPABILITIES : []
  return {
    account_access_state: accessState,
    capability_keys: capabilityKeys,
    access_epoch:
      accessState === "premium"
        ? `premium:${capabilityKeys.join(",")}`
        : `${accessState}:none`,
    entitlements:
      accessState === "premium"
        ? [
            {
              id: "4bfc8a77-7840-42fa-ad5f-60dafbdeafea",
              product_code: PRODUCT_CODE,
              product_display_name: "Premium",
              capability_keys: PREMIUM_CAPABILITIES,
              status: "active",
              starts_at: "2026-03-09T19:00:00Z",
              ends_at: "2026-04-09T19:00:00Z",
              revoked_at: null,
              revoked_reason_code: null
            }
          ]
        : []
  }
}

function buildProfileResponse(accessState: AccessState) {
  const response = clone(PROFILE_RESPONSE)
  if (accessState === "premium") {
    return response
  }

  const requiresAuth = accessState === "anonymous"
  response.analyst = {
    access: {
      state: "locked",
      capability_key: "premium_ai_analyst",
      reason_code: requiresAuth ? "anonymous_user" : "premium_capability_missing",
      product_codes: [PRODUCT_CODE],
      requires_auth: requiresAuth,
      requires_purchase: !requiresAuth,
      school_name: response.school.name
    },
    text: null,
    teaser_text:
      "Preview the first evidence-grounded analyst signals before unlocking the full Premium narrative.",
    disclaimer:
      "This analyst view is AI-generated from public government data. It highlights patterns in the published evidence, but it is not official advice or a recommendation."
  }
  response.neighbourhood = {
    access: {
      state: "locked",
      capability_key: "premium_neighbourhood",
      reason_code: requiresAuth ? "anonymous_user" : "premium_capability_missing",
      product_codes: [PRODUCT_CODE],
      requires_auth: requiresAuth,
      requires_purchase: !requiresAuth,
      school_name: response.school.name
    },
    area_context: null,
    teaser_text:
      "Premium neighbourhood context is available for this school, including deprivation context, local crime context, and house-price context."
  }

  return response
}

function buildCompareResponse(accessState: AccessState) {
  const response = clone(COMPARE_RESPONSE)
  if (accessState === "premium") {
    return response
  }

  const requiresAuth = accessState === "anonymous"
  response.access = {
    state: "locked",
    capability_key: "premium_comparison",
    reason_code: requiresAuth ? "anonymous_user" : "premium_capability_missing",
    product_codes: [PRODUCT_CODE],
    requires_auth: requiresAuth,
    requires_purchase: !requiresAuth,
    school_name: null
  }
  response.sections = []
  return response
}

async function gotoRoute(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: "domcontentloaded" })
}

async function registerPremiumJourneyRoutes(
  page: Page,
  state: PremiumJourneyState
): Promise<void> {
  await page.route("**/api/v1/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildSessionResponse(state.accessState))
    })
  })

  await page.route("**/api/v1/auth/start", async (route) => {
    const payload = route.request().postDataJSON() as { return_to?: string | null }
    state.accessState = "free"
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        redirect_url: payload.return_to ?? "/"
      })
    })
  })

  await page.route("**/api/v1/auth/signout", async (route) => {
    state.accessState = "anonymous"
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildSessionResponse("anonymous"))
    })
  })

  await page.route("**/api/v1/account/access", async (route) => {
    if (state.accessState === "anonymous") {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "authentication required" })
      })
      return
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildAccountAccessResponse(state.accessState))
    })
  })

  await page.route("**/api/v1/billing/products", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        products: [
          {
            code: PRODUCT_CODE,
            display_name: "Premium",
            description: "Launch bundle",
            billing_interval: "monthly",
            duration_days: null,
            capability_keys: PREMIUM_CAPABILITIES
          }
        ]
      })
    })
  })

  await page.route("**/api/v1/billing/checkout-sessions", async (route) => {
    const payload = route.request().postDataJSON() as {
      product_code: string
      success_path?: string | null
    }
    const successPath = payload.success_path ?? "/"
    const redirectUrl = new URL(successPath, "http://127.0.0.1:5173")
    redirectUrl.searchParams.set("checkout_id", CHECKOUT_ID)
    state.checkoutStatusPolls = 0

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        checkout_id: CHECKOUT_ID,
        product_code: payload.product_code,
        status: "open",
        redirect_url: `${redirectUrl.pathname}${redirectUrl.search}`,
        expires_at: "2026-03-09T20:00:00Z",
        account_access_state:
          state.accessState === "premium" ? "premium" : "free"
      })
    })
  })

  await page.route(`**/api/v1/billing/checkout-sessions/${CHECKOUT_ID}`, async (route) => {
    state.checkoutStatusPolls += 1

    if (state.checkoutStatusPolls === 1) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          checkout_id: CHECKOUT_ID,
          product_code: PRODUCT_CODE,
          status: "processing_payment",
          redirect_url: null,
          expires_at: "2026-03-09T20:00:00Z",
          account_access_state: "free"
        })
      })
      return
    }

    state.accessState = "premium"
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        checkout_id: CHECKOUT_ID,
        product_code: PRODUCT_CODE,
        status: "completed",
        redirect_url: null,
        expires_at: "2026-03-09T20:00:00Z",
        account_access_state: "premium"
      })
    })
  })

  await page.route("**/api/v1/schools/100001/trends", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(clone(TRENDS_RESPONSE))
    })
  })

  await page.route("**/api/v1/schools/100001/trends/dashboard", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(clone(DASHBOARD_RESPONSE))
    })
  })

  await page.route("**/api/v1/schools/100001", async (route) => {
    state.profileRequestCount += 1
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildProfileResponse(state.accessState))
    })
  })

  await page.route("**/api/v1/schools/compare?**", async (route) => {
    state.compareRequestCount += 1
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildCompareResponse(state.accessState))
    })
  })
}

test("premium profile journey unlocks after checkout and relocks after sign-out", async ({
  page
}) => {
  const state: PremiumJourneyState = {
    accessState: "anonymous",
    checkoutStatusPolls: 0,
    profileRequestCount: 0,
    compareRequestCount: 0
  }
  await registerPremiumJourneyRoutes(page, state)

  await gotoRoute(page, "/sign-in?returnTo=%2Fschools%2F100001")
  await page.getByLabel("Email address").fill(USER_EMAIL)
  await page.getByRole("button", { name: "Continue" }).click()

  await expect(page).toHaveURL(/\/schools\/100001$/)
  await expect(
    page.getByRole("heading", {
      name: "Camden Bridge Primary School",
      exact: true
    })
  ).toBeVisible({ timeout: 10000 })
  await expect(page.getByText("Analyst Preview")).toBeVisible()
  await expect(
    page.getByText(
      "Preview the first evidence-grounded analyst signals before unlocking the full Premium narrative."
    )
  ).toBeVisible()
  await expect(
    page.getByText(
      "The published profile points to a school with more stability than volatility across the current evidence base."
    )
  ).toHaveCount(0)
  await expect(page.getByRole("banner").getByText("Premium")).toHaveCount(0)

  await page.getByRole("link", { name: "View Premium plans" }).first().click()
  await expect(page).toHaveURL(/\/account\/upgrade/)
  await page.getByRole("button", { name: "View Premium plans" }).click()

  await expect(
    page.getByRole("heading", { name: "Checkout status" })
  ).toBeVisible()
  await expect(page.getByRole("button", { name: "Continue" })).toBeVisible({
    timeout: 7000
  })
  expect(state.checkoutStatusPolls).toBeGreaterThanOrEqual(2)

  await page.getByRole("button", { name: "Continue" }).click()

  await expect(page).toHaveURL(/\/schools\/100001$/)
  await expect(page.getByText("Analyst Summary")).toBeVisible()
  await expect(
    page.getByText(
      "The published profile points to a school with more stability than volatility across the current evidence base."
    )
  ).toBeVisible()
  await expect(page.getByText("Area Deprivation")).toBeVisible()
  await expect(page.getByRole("banner").getByText("Premium")).toBeVisible()
  expect(state.profileRequestCount).toBeGreaterThanOrEqual(2)

  await page.getByRole("button", { name: "Sign out" }).click()

  await expect(page.getByText("Analyst Preview")).toBeVisible()
  await expect(
    page.getByRole("link", { name: "Sign in to continue" }).first()
  ).toBeVisible()
  await expect(
    page.getByText(
      "The published profile points to a school with more stability than volatility across the current evidence base."
    )
  ).toHaveCount(0)
  await expect(page.getByRole("banner").getByText("Premium")).toHaveCount(0)
  expect(state.profileRequestCount).toBeGreaterThanOrEqual(3)
})

test("locked compare upgrades cleanly into the full comparison matrix", async ({
  page
}) => {
  const state: PremiumJourneyState = {
    accessState: "free",
    checkoutStatusPolls: 0,
    profileRequestCount: 0,
    compareRequestCount: 0
  }
  await registerPremiumJourneyRoutes(page, state)

  await gotoRoute(page, "/compare?urns=100001,200002")

  await expect(
    page.getByRole("heading", {
      name: "Compare schools side by side with Premium"
    })
  ).toBeVisible()
  await page.getByRole("link", { name: "View Premium plans" }).click()

  await expect(page).toHaveURL(/\/account\/upgrade/)
  await page.getByRole("button", { name: "View Premium plans" }).click()
  await expect(page.getByRole("button", { name: "Continue" })).toBeVisible({
    timeout: 7000
  })

  await page.getByRole("button", { name: "Continue" }).click()

  await expect(page).toHaveURL(/\/compare\?urns=100001(?:%2C|,)200002$/)
  await expect(page.getByRole("heading", { name: "Inspection" })).toBeVisible()
  await expect(
    page.getByRole("heading", {
      name: "Compare schools side by side with Premium"
    })
  ).toHaveCount(0)
  expect(state.compareRequestCount).toBeGreaterThanOrEqual(2)
})
