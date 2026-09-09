import { cleanup } from "@testing-library/react";
import * as matchers from "@testing-library/jest-dom/matchers";
import { afterAll, afterEach, beforeAll } from "vitest";
import { expect } from "vitest";
import { setupServer } from "msw/node";

import { handlers } from "./server";

expect.extend(matchers);

export const server = setupServer(...handlers);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());
