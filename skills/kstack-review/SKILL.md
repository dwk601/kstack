---
name: kstack-review
description: Review plans and code independently with evidence.
disable-model-invocation: true
---

# kstack-review

Shared rules: read `../kstack/SKILL.md` first.

Fresh configured reviewer, never the implementer.

- **Plan:** check code facts/scope/file ownership/dependencies/acceptance; identify chat plan, not SHAs.
- **Task:** pin base/head; judge one task's diff against acceptance; run task checks/lint.
- **Audit:** at frozen head, judge gaps beyond task reviews: cross-task interactions/integration edits/unreviewed changes/request scope/regressions. Validate gate evidence; probe, don't rerun suites.

Trace callers/data/wire formats/flags/dependencies/config/shared state beyond the diff. Prove safety assumptions with code/runtime proof; cite applicable repo rules; check correctness/edges/root cause/complexity. User-visible change without matching map update: FAIL if repo has a map.

FAIL only if new in diff: workaround-justifying comments, quick-fix timers/sleeps, lint/type suppressions, deprecated-pattern copies. Give root-cause fixes. Inline reason/expiry date/named human approval exempt these. Machine-checkable FAILs: kstack-improve candidates.

Return `task/lane | base/head | PASS/FAIL/BLOCKED | checks + evidence`.
FAIL: all findings your run proved; drop others; merge findings by root cause. Give severity, file:line, criterion, evidence, fix. BLOCKED: missing checks/errors; style cannot block. Two imagined edits per test: broken behavior → fail; new internals, same observable results → pass. Missing tests fail only in repo-tested areas with unproven behavior.
