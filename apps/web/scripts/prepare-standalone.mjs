import {
  cpSync,
  existsSync,
  readlinkSync,
  readdirSync,
  statSync,
  symlinkSync,
  unlinkSync,
} from "node:fs";
import { dirname, isAbsolute, relative, resolve } from "node:path";

const appRoot = resolve(import.meta.dirname, "..");
const candidates = [
  resolve(appRoot, ".next", "standalone", "apps", "web", "server.js"),
  resolve(appRoot, ".next", "standalone", "server.js"),
];
const serverEntry = candidates.find(existsSync);

if (!serverEntry) {
  throw new Error("Standalone server not found after the Next.js build.");
}

const runtimeRoot = dirname(serverEntry);
const staticSource = resolve(appRoot, ".next", "static");
const publicSource = resolve(appRoot, "public");

function normalizeWindowsDirectoryLinks(directory, standaloneRoot) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const entryPath = resolve(directory, entry.name);
    if (entry.isSymbolicLink()) {
      const targetPath = resolve(directory, readlinkSync(entryPath));
      const targetRelativePath = relative(standaloneRoot, targetPath);
      if (targetRelativePath.startsWith("..") || isAbsolute(targetRelativePath)) {
        throw new Error(`Standalone link target escapes the runtime root: ${entryPath}`);
      }
      if (statSync(targetPath).isDirectory()) {
        unlinkSync(entryPath);
        symlinkSync(targetPath, entryPath, "junction");
      }
      continue;
    }
    if (entry.isDirectory()) normalizeWindowsDirectoryLinks(entryPath, standaloneRoot);
  }
}

if (process.platform === "win32") {
  const standaloneRoot = resolve(appRoot, ".next", "standalone");
  normalizeWindowsDirectoryLinks(standaloneRoot, standaloneRoot);
}

cpSync(staticSource, resolve(runtimeRoot, ".next", "static"), { recursive: true });
if (existsSync(publicSource)) {
  cpSync(publicSource, resolve(runtimeRoot, "public"), { recursive: true });
}
