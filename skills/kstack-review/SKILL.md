---
name: kstack-review
description: Independently review plans and code with evidenced verdicts.
disable-model-invocation: true
---

# kstack-review

Shared rules: read `../kstack/SKILL.md` first.

Use a fresh configured reviewer, not the implementer.

- **Plan:** check code facts, scope, file ownership, dependencies and acceptance; identify the chat plan, not SHAs.
- **Task:** pin base/head; judge one task's diff against acceptance; run task checks/lint.
- **Audit:** at frozen head, judge what task reviews cannot: cross-task interactions, integration edits, unreviewed changes, request scope/regressions. Validate gate evidence; probe, don't rerun suites.

Trace callers, data/wire formats, flags, dependencies, config/shared state beyond the diff. Prove safety with code/runtime evidence and repo rules; check correctness, edges, root cause, complexity.

FAIL new-in-diff workaround-justifying comments, quick-fix timers/sleeps, lint/type suppressions and deprecated-pattern copies; give root-cause fixes. Inline reason, expiry date and named human approval exempt these. Machine-checkable FAILs: kstack-improve candidates.

Return `task/lane | base/head | PASS/FAIL/BLOCKED | checks + evidence`.
FAIL: all proven findings: severity, file:line, criterion, evidence, fix. BLOCKED: missing checks/errors; style cannot block. Flag behavior-blind or internals-coupled tests. Missing tests fail only in repo-tested areas with unproven behavior.
