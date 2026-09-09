import assert from "node:assert/strict";
import test from "node:test";

import { createUmiEnvironment } from "./run-umi.mjs";

test("defaults the Admin development server to the loopback interface", () => {
  const environment = createUmiEnvironment({ PATH: "test-path" });
  assert.equal(environment.HOST, "localhost");
  assert.equal(environment.PORT, "3001");
  assert.equal(environment.PATH, "test-path");
});

test("preserves explicit host and port overrides", () => {
  const environment = createUmiEnvironment({ HOST: "192.0.2.10", PORT: "4100" });
  assert.equal(environment.HOST, "192.0.2.10");
  assert.equal(environment.PORT, "4100");
});
