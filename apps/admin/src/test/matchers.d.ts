import type { TestingLibraryMatchers } from "@testing-library/jest-dom/matchers";
import "vitest";

// Augment this application's Vitest when workspace consumers use different majors.
declare module "vitest" {
  interface Assertion<T = unknown> extends TestingLibraryMatchers<unknown, T> {}
  interface AsymmetricMatchersContaining extends TestingLibraryMatchers<unknown, unknown> {}
}
