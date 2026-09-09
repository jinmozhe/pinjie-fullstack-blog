import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const guard = resolve(import.meta.dirname, "check-typescript-boundaries.mjs");
const fixtureRoot = mkdtempSync(resolve(tmpdir(), "pinjie-typescript-boundaries-"));

function write(path, content) {
  const target = resolve(fixtureRoot, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content, "utf8");
}

function runGuard() {
  return spawnSync(process.execPath, [guard, "--root", fixtureRoot], {
    encoding: "utf8",
    windowsHide: true,
  });
}

try {
  write("apps/web/src/features/auth/index.ts", "export const login = true;\n");
  write("apps/web/src/features/users/example.ts", 'import { login } from "@/features/auth";\nexport { login };\n');
  const valid = runGuard();
  if (valid.status !== 0) throw new Error(`Expected public Feature import to pass.\n${valid.stderr}`);

  write("apps/web/src/features/auth/internal.ts", "export const secret = true;\n");
  write(
    "apps/web/src/features/users/example.ts",
    'export async function load() { return import("@/features/auth/internal"); }\n',
  );
  const dynamicInternal = runGuard();
  if (dynamicInternal.status === 0) throw new Error("Expected dynamic cross-Feature internal import to fail.");

  write("apps/web/src/features/users/example.ts", "export const user = true;\n");
  write("apps/web/src/lib/a.ts", 'import "./b";\n');
  write("apps/web/src/lib/b.ts", 'import "./a";\n');
  const cycle = runGuard();
  if (cycle.status === 0) throw new Error("Expected a TypeScript dependency cycle to fail.");

  write("apps/web/src/lib/b.ts", "export const value = true;\n");
  write("apps/admin/src/example.ts", 'import "../../web/src/lib/a";\n');
  const crossApplication = runGuard();
  if (crossApplication.status === 0) throw new Error("Expected a cross-application relative import to fail.");

  console.log("TypeScript boundary fixtures passed: public entry, dynamic internal import, cycle, and application isolation.");
} finally {
  rmSync(fixtureRoot, { recursive: true, force: true });
}
