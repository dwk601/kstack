---
name: kstack-verify
description: Exercise real behavior and return revision-bound outcomes in chat.
disable-model-invocation: true
---

# kstack-verify

Shared rules: read `../kstack/SKILL.md` first.

1. Pin revision, scenario and pass condition. Use real e2e/API/CLI recipes from project config, scripts, docs or CI.
2. Isolate checkout, instance, port, data and account; keep production data untouched. Wait for the scenario's first step, not an open port.
3. Drive real interactions and check responses/side effects against acceptance. Avoid captures; unavoidable data follows shared owned scratch rules.
4. Compare matching base/head workloads. If base lacks the feature, verify head's end state without inventing a baseline.

Return `base/head | PASS/FAIL/BLOCKED | commands | observations | cleanup` in stdout/chat. Required behavior that cannot run, wrong interaction method or inconclusive evidence is BLOCKED. N/A needs an inapplicability reason.

Stop only your processes; use shared cleanup safeguards/readback. Offer missing recipes after standalone success; swarm lanes report them without editing config.
