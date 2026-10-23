---
name: kstack-debug
description: Reproduce bugs and fix evidenced causes.
disable-model-invocation: true
---

# kstack-debug

Shared rules: read `../kstack/SKILL.md` first.

1. Reproduce at the failing UI/CLI/API/job; name inaccessible surfaces. Diagnosis-only leaves source unchanged, including instrumentation.
2. Test competing hypotheses with logs, probes, bisect or a debugger. Locate the first wrong decision. After two failed fixes, test the premise directly.
3. Diagnosis-only stops at the cause. Otherwise fix the producer, using guards only for legitimate states; cover the same fault within scope and revert disproved experiments.
4. Rerun the original reproduction; focused regressions should fail before and pass after.

Report symptom, cause evidence and before/after results.
