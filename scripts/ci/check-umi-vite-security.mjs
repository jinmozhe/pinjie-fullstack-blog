import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const require = createRequire(import.meta.url);
const pnpmfile = require(resolve(root, ".pnpmfile.cjs"));
const readPackage = pnpmfile.hooks.readPackage;

const transformed = readPackage({
  name: "@umijs/preset-umi",
  version: "4.7.5",
  dependencies: {
    "@umijs/bundler-vite": "4.7.5",
    "@umijs/bundler-webpack": "4.7.5",
  },
});
assert.equal(transformed.dependencies["@umijs/bundler-vite"], undefined);
assert.equal(transformed.dependencies["@umijs/bundler-webpack"], "4.7.5");
assert.throws(
  () => readPackage({ name: "@umijs/preset-umi", version: "4.7.6", dependencies: {} }),
  /Re-evaluate the Webpack-only security patch/,
);

const lockfile = await readFile(resolve(root, "pnpm-lock.yaml"), "utf8");
for (const forbidden of ["'@umijs/bundler-vite@4.7.5':", "vite@4.5.2:"]) {
  assert.equal(lockfile.includes(forbidden), false, `Forbidden dependency remains in pnpm-lock.yaml: ${forbidden}`);
}
assert.equal(lockfile.includes("vite@6.4.3:"), true, "The supported Vitest Vite version is missing");

const patch = await readFile(resolve(root, "patches", "@umijs__preset-umi@4.7.5.patch"), "utf8");
assert.match(patch, /Umi Vite bundler is disabled because its supported Vite version has known High vulnerabilities/);
assert.match(patch, /-var import_schema = require\("@umijs\/bundler-vite\/dist\/schema"\);/);
assert.match(patch, /-var bundlerVite = .*"@umijs\/bundler-vite"/);

const webpackPatch = await readFile(resolve(root, "patches", "@umijs__bundler-webpack@4.7.5.patch"), "utf8");
assert.match(webpackPatch, /server\.listen\(port, opts\.host/);

process.stdout.write("Umi Webpack-only dependency and loopback policies passed.\n");
