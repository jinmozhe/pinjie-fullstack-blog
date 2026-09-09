import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { idPattern, repository, requireCondition, validateHandoff } from "./composition.mjs";

export function run(command, args, options = {}) {
  const spawnOptions = { encoding: "utf8", timeout: 120_000, maxBuffer: 16 * 1024 * 1024,
    ...options, shell: false, windowsHide: true };
  let result;
  switch (command) {
    case "git": result = spawnSync("git", args, spawnOptions); break;
    case "gh": result = spawnSync("gh", args, spawnOptions); break;
    case "docker": result = spawnSync("docker", args, spawnOptions); break;
    case process.execPath: result = spawnSync(process.execPath, args, spawnOptions); break;
    default: throw new Error("Unsupported release subprocess.");
  }
  requireCondition(!result.error && result.status === 0, `${command} failed (${result.status ?? "launch error"}).`);
  return result.stdout?.trim() ?? "";
}

export function githubRun(runId, workflow, defaultBranch) {
  requireCondition(idPattern.test(String(runId)), "Invalid GitHub Run ID.");
  const data = JSON.parse(run("gh", ["api", `repos/${repository}/actions/runs/${runId}`]));
  requireCondition(data.event === "workflow_dispatch" && data.conclusion === "success" &&
    data.path === `.github/workflows/${workflow}` && data.head_branch === defaultBranch &&
    data.head_repository?.full_name === repository, "Run is not a successful trusted default-branch workflow.");
  return data;
}

export function downloadEvidence(runId, artifact, directory, filename) {
  run("gh", ["run", "download", String(runId), "--repo", repository, "--name", artifact, "--dir", directory]);
  return JSON.parse(readFileSync(resolve(directory, filename), "utf8"));
}

export function trustedHandoff(image, defaultBranch, directory) {
  const source = image.release.source.commit_sha;
  const data = githubRun(image.handoff_run_id, "publish-images.yml", defaultBranch);
  const evidence = downloadEvidence(image.handoff_run_id, `source-handoff-${source}-${data.run_attempt}`, directory, "handoff.json");
  validateHandoff(evidence, source, image.handoff_run_id, data.run_attempt);
  return evidence;
}
