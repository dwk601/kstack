---
name: kstack-review
description: Independently review plans and code with evidenced verdicts.
disable-model-invocation: true
---

# kstack-review

Shared rules: read `../kstack/SKILL.md` first.

Use a fresh configured reviewer, not the implementer. Leave source/tests unchanged.

- **Plan:** check code facts, scope, file ownership, dependencies and acceptance; identify the chat plan, not SHAs.
- **Code:** pin base/head, compare the task diff to acceptance and run task checks/lint.
- **Audit:** inspect the combined diff for assigned scope/regressions. Validate gate evidence and run focused probes, not unrelated suites.

Trace callers, data/wire formats, flags, dependencies, config and shared state beyond the diff. Prove safety assumptions with code/runtime evidence; cite applicable repo rules. Check correctness, edges, root cause and complexity.

Return `task/lane | base/head | PASS/FAIL/BLOCKED | checks + evidence`.
FAIL collects all proven findings: severity, file:line, broken criterion, evidence and fix. BLOCKED names missing checks/errors; style alone does not block. Flag tests insensitive to broken behavior or coupled to internals. Missing tests fail only when the repo tests that area and behavior remains unproven.
