---
name: kstack-understand
description: Explain how and why code works, with evidence.
disable-model-invocation: true
---

# kstack understand

Shared rules: read `../kstack/SKILL.md` first.

Read-only; answer at requested depth.

1. Follow entrypoints, callers, data shapes, state, side effects, config and tests.
2. For why, inspect `git log -L`/`git blame`, shaping commits/PRs (`gh pr view`) and linked issues.
3. Separate observations from inference; name missing evidence.

Return overview, ordered execution path, file:line locations, gotchas and questions. Omit empty sections.
