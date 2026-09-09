import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptPath = fileURLToPath(import.meta.url);
const appRoot = resolve(dirname(scriptPath), "..");
const maxCLI = resolve(
  appRoot,
  "node_modules",
  "@umijs",
  "max",
  "bin",
  "max.js",
);

export function createUmiEnvironment(environment = process.env) {
  return {
    ...environment,
    HOST: environment.HOST ?? "localhost",
    PORT: environment.PORT ?? "3001",
  };
}

function run() {
  const child = spawn(
    process.execPath,
    [maxCLI, "dev", ...process.argv.slice(2)],
    {
      cwd: appRoot,
      env: createUmiEnvironment(),
      shell: false,
      stdio: "inherit",
      windowsHide: true,
    },
  );

  child.once("error", (error) => {
    process.stderr.write(`${error}\n`);
    process.exitCode = 1;
  });
  child.once("exit", (code, signal) => {
    process.exitCode = code ?? (signal ? 1 : 0);
  });
}

if (process.argv[1] && resolve(process.argv[1]) === scriptPath) {
  run();
}
