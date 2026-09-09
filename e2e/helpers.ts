import AxeBuilder from "@axe-core/playwright";
import { expect, type Page } from "@playwright/test";

export async function expectPageQuality(page: Page): Promise<void> {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.keyboard.press("Tab");
  expect(await page.evaluate(() => document.activeElement?.tagName ?? "BODY")).not.toBe("BODY");
  const accessibilityScan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(accessibilityScan.violations).toEqual([]);
}

export async function expectNoClientTokenPersistence(page: Page): Promise<void> {
  const persistedValues = await page.evaluate(() => [
    ...Object.entries(localStorage),
    ...Object.entries(sessionStorage),
  ]);
  expect(JSON.stringify(persistedValues)).not.toMatch(/access.?token|refresh.?token|eyJ[A-Za-z0-9_-]{20,}/i);
  expect(await page.content()).not.toMatch(/eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}/);
}

export async function expectCookieProfile(
  page: Page,
  names: { access: string; refresh: string; csrf: string },
): Promise<string> {
  const cookies = await page.context().cookies();
  const access = cookies.find((cookie) => cookie.name === names.access);
  const refresh = cookies.find((cookie) => cookie.name === names.refresh);
  const csrf = cookies.find((cookie) => cookie.name === names.csrf);
  expect(access).toMatchObject({ httpOnly: true, sameSite: "Lax" });
  expect(refresh).toMatchObject({ httpOnly: true, sameSite: "Lax" });
  expect(csrf).toMatchObject({ httpOnly: false, sameSite: "Lax" });
  expect(csrf?.value).toBeTruthy();
  return csrf!.value;
}

export function uniqueUsername(prefix: string, projectName: string): string {
  const suffix = `${projectName}-${Date.now()}`.toLowerCase().replace(/[^a-z0-9-]/g, "-");
  return `${prefix}-${suffix}`.slice(0, 50);
}
