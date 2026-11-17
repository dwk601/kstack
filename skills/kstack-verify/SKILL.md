---
name: kstack-verify
description: Exercise real behavior and return revision-bound outcomes in chat.
disable-model-invocation: true
---

# kstack-verify

Shared rules: read `../kstack/SKILL.md` first.

1. Pin revision/scenario/pass condition; use project `verify`, `.kstack/verify/` or real e2e/API/CLI recipes from scripts/docs/CI.
2. Isolate checkout/instance/port/data/account; no production data. Launch; wait for the scenario's first step, not an open port. Doctor first: read-only ownership/health; block on failure.
3. Drive real interactions (EVERY mapped feature by default); check responses/side effects against acceptance. Project `verify.affected_only=true` alone permits `paths` narrowing to affected features plus one smoke feature; unknowns need all. Proof: shared owned scratch rules.
4. Compare matching base/head workloads; if absent on base, prove head's end state, not an invented baseline.

Return `base/head | PASS/FAIL/BLOCKED | commands | observations | cleanup` in stdout/chat. Required behavior that cannot run, wrong interaction method or inconclusive evidence is BLOCKED. N/A needs an inapplicability reason.

Stop only your processes; use shared cleanup safeguards/readback. Run project teardown. Offer missing recipes after standalone success; no map: offer kstack-setup harness. Swarm lanes report without config edits.
