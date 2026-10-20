---
name: kstack-review
description: Review plans and code independently with evidenced verdicts.
disable-model-invocation: true
---

# kstack review

Shared rules: read `../kstack/SKILL.md` first.

Never review your implementation; dispatch a fresh configured reviewer. Never edit source/tests.

## Modes

- **plan**: check scope, code facts, file overlap, dependencies, parallelism and observable acceptance. No revision required yet.
- **code**: review exact base/head against task.
- **audit**: inspect combined diff for assigned scope, cross-task behavior or regression focus. Verify evidence and reproduce relevant claims; don't trust summaries.

## Method

1. Record base/head SHAs. Code reviews run task checks/lint; audits inspect gates evidence and run focused probes without repeating unrelated suites.
2. Compare diff to acceptance. Follow callers, stored data, wire formats, flags, library source, config and shared state beyond changed files. Name the fact safety depends on and prove it by running code. Find applicable repo standards; cite rules supporting findings.
3. Check correctness, edges, root cause, complexity and behavioral evidence.

## Verdict

Return `task or lane | base/head SHAs | PASS/FAIL/BLOCKED | checks | evidence`; plan reviews identify the chat plan instead of SHAs.

FAIL lists all proven findings together: severity, file:line, broken criterion, evidence, fix. BLOCKED names missing check/error. Style does not block. Tests that pass when behavior breaks, or fail on internal-only changes, are findings. Missing tests fail only where the repo tests that area and behavior remains unproven.
