---
name: kstack-debug
description: Reproduce bugs; fix evidenced causes.
disable-model-invocation: true
---

# kstack-debug

Shared rules: read `../kstack/SKILL.md` first.

1. Reproduce failing UI/CLI/API/job; name inaccessible surfaces. Diagnosis-only: no source edits, even instrumentation.
2. Test rival hypotheses via logs/probes/bisect/debugger; find the first wrong decision. Two failed fixes: test the premise directly. Deep-dig deciding fact: propose a cheap always-on signal.
3. Diagnosis-only: stop at cause. Else fix the producer; guards/retries/swallowed errors/clamped values/discarded state hide bugs unless states are legitimate. Cover same fault within scope; revert disproved experiments.
4. Rerun original repro; focused regressions must fail before/pass after.

Report symptom, cause evidence and before/after results.
