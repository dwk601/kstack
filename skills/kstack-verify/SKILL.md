---
name: kstack-verify
description: Prove a change works by running the real app or tool as a user would, and keep the evidence. Use when the user invokes kstack-verify.
disable-model-invocation: true
---

# kstack verify

Shared rules: read `../kstack/SKILL.md` first.

1. Find how the project runs: `verify` in `.kstack/project.json`, README, package scripts, Makefile, CI. Prefer existing harnesses: e2e tests, scripts, HTTP endpoints, the CLI itself.
2. Start an isolated instance: its own port, data directory, and test account. Wait until it is usable, not just started. Never touch production data.
3. Drive the feature the way a user does. Capture the action and the result: output, screenshot, response body, database row, file written.
4. Check side effects, not just what is visible.
5. Stop only what you started, by PID. Keep the evidence and report its path.

Report: commands run, revision, what you saw, evidence paths, and what you could not verify and why. Wrong surface or inconclusive is not a pass.

If the project has no recipe, offer to add one to `.kstack/project.json` after a run works.
