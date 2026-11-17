---
name: kstack-review
description: Review plans and code independently with evidence.
disable-model-invocation: true
---

# kstack-review

Shared rules: read `../kstack/SKILL.md` first.

Use a fresh configured reviewer, not the implementer.

- **Plan:** check code facts/scope/file ownership/dependencies/acceptance; identify chat plan, not SHAs.
- **Task:** pin base/head; judge one task's diff against acceptance; run task checks/lint.
- **Audit:** at frozen head, judge what task reviews cannot: cross-task interactions, integration edits, unreviewed changes, request scope/regressions. Validate gate evidence; probe, don't rerun suites.

Trace callers, data/wire formats, flags, dependencies, config/shared state beyond the diff. Prove safety assumptions with code/runtime evidence; cite repo rules; check correctness, edges, root cause, complexity. With a feature map, a user-visible change without a matching map update is FAIL.

For all four, FAIL only when new in the diff: workaround-justifying comments, quick-fix timers/sleeps, lint/type suppressions, deprecated-pattern copies. Give root-cause fixes. Inline reason/expiry date/named human approval exempt these. Machine-checkable FAILs: kstack-improve candidates.

Return `task/lane | base/head | PASS/FAIL/BLOCKED | checks + evidence`.
FAIL: all proven findings: severity, file:line, criterion, evidence, fix. BLOCKED: missing checks/errors; style cannot block. Flag behavior-blind or internals-coupled tests. Missing tests fail only in repo-tested areas with unproven behavior.
