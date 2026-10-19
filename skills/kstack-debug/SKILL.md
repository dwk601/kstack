---
name: kstack-debug
description: Diagnose bugs from runtime evidence and fix the cause.
disable-model-invocation: true
---

# kstack debug

Shared rules: read `../kstack/SKILL.md` first. Standalone fixes enter Plan and Execute; assigned workers use the steps below. Diagnosis-only requests never edit source; use runtime probes and report if source instrumentation is required.

1. Reproduce it where it happens: UI, CLI, API, or job. If it will not reproduce, narrow the conditions or add logging until it does. If you cannot reach that surface, say why.
2. List hypotheses. Test the one that cuts the most: logs, a probe script, `git bisect`, a debugger. Drop what the evidence rules out.
3. Name the mechanism before fixing. If two fixes built on one assumption failed, question the assumption. If the user asked only for a diagnosis, stop here.
4. Make the smallest fix the evidence supports. Revert anything a disproved hypothesis added.
5. Rerun the original reproduction. Add a regression test when one is cheap and clear, and verify it fails on the unfixed code and passes with the fix.

Report: symptom, root cause with evidence, fix, and the before and after output.
