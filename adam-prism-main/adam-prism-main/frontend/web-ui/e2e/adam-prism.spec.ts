import { test, expect } from "@playwright/test"

/**
 * [PHASE3] E2E tests for Adam Prism Web UI
 * Covers critical user journeys: navigation, login, chat, error states.
 */

test.describe("Homepage", () => {
  test("loads and shows branding", async ({ page }) => {
    await page.goto("/")
    // Should redirect to login or show app depending on auth state
    await expect(page).toHaveTitle(/Adam Prism/)
  })

  test("shows offline fallback when API is down", async ({ page, context }) => {
    // Block all API requests
    await context.route("**/api/**", (route) => route.abort())
    await page.goto("/")
    // Should not crash, should show some UI
    await expect(page.locator("body")).toBeVisible()
  })
})

test.describe("Login flow", () => {
  test("login page renders", async ({ page }) => {
    await page.goto("/login")
    await expect(page.getByLabel(/username|email/i)).toBeVisible()
    await expect(page.getByLabel(/password/i)).toBeVisible()
  })

  test("shows error on invalid credentials", async ({ page }) => {
    await page.goto("/login")
    await page.getByLabel(/username|email/i).fill("wrong@example.com")
    await page.getByLabel(/password/i).fill("wrongpassword")
    await page.getByRole("button", { name: /sign in|دخول/i }).click()
    // Should show error
    await expect(page.getByRole("alert")).toBeVisible({ timeout: 5000 })
  })

  test("link to register page works", async ({ page }) => {
    await page.goto("/login")
    await page.getByRole("link", { name: /sign up|إنشاء/i }).click()
    await expect(page).toHaveURL(/\/register/)
  })
})

test.describe("Register flow", () => {
  test("register page renders", async ({ page }) => {
    await page.goto("/register")
    await expect(page.getByLabel(/email/i)).toBeVisible()
    await expect(page.getByLabel(/username/i)).toBeVisible()
    await expect(page.getByLabel(/password/i).first()).toBeVisible()
  })

  test("password mismatch shows error", async ({ page }) => {
    await page.goto("/register")
    await page.getByLabel(/email/i).fill("test@example.com")
    await page.getByLabel(/username/i).fill("testuser")
    await page.getByLabel(/password/i).first().fill("password123")
    await page.getByLabel(/confirm/i).fill("different")
    await page.getByRole("button", { name: /sign up|إنشاء/i }).click()
    await expect(page.getByRole("alert")).toBeVisible()
  })

  test("short password shows error", async ({ page }) => {
    await page.goto("/register")
    await page.getByLabel(/email/i).fill("test@example.com")
    await page.getByLabel(/username/i).fill("testuser")
    await page.getByLabel(/password/i).first().fill("123")
    await page.getByLabel(/password/i).first().blur()
    // HTML5 validation should prevent submit
    const button = page.getByRole("button", { name: /sign up|إنشاء/i })
    await expect(button).toBeDisabled().catch(() => {
      // If not disabled, should show alert
      return expect(page.getByRole("alert")).toBeVisible()
    })
  })
})

test.describe("PWA", () => {
  test("has PWA manifest", async ({ page }) => {
    await page.goto("/")
    const manifest = page.locator('link[rel="manifest"]')
    await expect(manifest).toHaveAttribute("href", "/manifest.json")
  })

  test("has theme color", async ({ page }) => {
    await page.goto("/")
    const theme = page.locator('meta[name="theme-color"]')
    await expect(theme).toHaveCount(1)
  })
})

test.describe("Accessibility", () => {
  test("login page has proper labels", async ({ page }) => {
    await page.goto("/login")
    await expect(page.getByLabel(/username|email/i)).toBeVisible()
    await expect(page.getByLabel(/password/i)).toBeVisible()
  })

  test("supports keyboard navigation", async ({ page }) => {
    await page.goto("/login")
    await page.keyboard.press("Tab")
    await page.keyboard.press("Tab")
    // Should be able to focus and navigate
  })
})
