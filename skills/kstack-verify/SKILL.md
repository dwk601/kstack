---
name: kstack-verify
description: Exercise real behavior and return revision-bound outcomes in chat.
disable-model-invocation: true
---

# kstack-verify

Shared rules: read `../kstack/SKILL.md` first.

1. Pin revision/scenario/pass condition; use project `verify`, `.kstack/verify/` or real e2e/API/CLI recipes from scripts/docs/CI.
2. Isolate checkout/instance/port/data/account; no production data. Launch to usable state, not an open port. Doctor first (read-only ownership/health); failures block driving.
3. Drive EVERY mapped feature (sub-features/entry points) by default; check real responses/side effects/end state against acceptance. `paths` may narrow to affected features plus one smoke feature only with project `verify.affected_only=true`; unknowns need all. Proof captures: shared exception only.
4. Compare matching base/head workloads; if absent on base, prove head's end state, not an invented baseline.

Return `base/head | PASS/FAIL/BLOCKED | commands | observations | cleanup` in stdout/chat. Unrunnable required behavior, wrong interaction method or inconclusive evidence: BLOCKED. N/A needs an inapplicability reason.

Stop only your processes; use shared cleanup safeguards/readback. No map: offer kstack-setup harness after standalone success; swarm lanes report without config edits.
