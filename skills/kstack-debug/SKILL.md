---
name: kstack-debug
description: Diagnose bugs from runtime evidence and fix the cause.
disable-model-invocation: true
---

# kstack debug

Shared rules: read `../kstack/SKILL.md` first. Diagnosis-only never edits source; report when source instrumentation is needed.

1. Reproduce at the failing UI/CLI/API/job. Narrow conditions or use transient stdout instrumentation until reproducible. Explain inaccessible surfaces.
2. List hypotheses; test the most discriminating with existing logs, probes, bisect or debugger. Drop disproved hypotheses.
3. Name the mechanism before fixing. Two failed fixes on one assumption mean question it. Diagnosis-only stops here.
4. Apply the smallest supported fix; revert disproved experiments.
5. Rerun original reproduction. Add cheap, clear regressions and prove they fail before/pass after.

Report symptom, evidenced cause, fix and before/after output.
