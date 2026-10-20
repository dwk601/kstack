---
name: kstack-verify
description: Exercise real behavior and return revision-bound outcomes in chat.
disable-model-invocation: true
---

# kstack verify

Shared rules: read `../kstack/SKILL.md` first.

1. Pin revision, scenario and concrete pass condition. Find real recipes in `.kstack/project.json`, docs, scripts or CI; prefer existing e2e/API/CLI drivers.
2. Isolate checkout, instance, port, data and test account. Wait for the scenario's first step, not merely an open port. Never touch production data or edit source as a verifier.
3. Drive real user interactions; describe output, responses and side effects in chat. Judge the pass condition, not process startup. Avoid captures; unavoidable minimal test/screenshot data uses shared owned scratch rules.
4. Compare like behavior on base/head. If base lacks the feature, say so and verify head's added behavior/end state. Never invent baselines or ratios between different workloads.
5. Before returning, apply shared cleanup and Finish safety/readback rules. Stop only your processes; preserve revision-bound outcomes in conversation. Unsafe removal means partial cleanup.

Return `base/head SHAs | PASS/FAIL/BLOCKED | commands | observations | outcomes | diagnostic scratch cleanup` in stdout/chat. Required behavior that cannot run, wrong interaction method or inconclusive evidence is BLOCKED. N/A requires genuine inapplicability and reason.

After standalone success, offer to save a missing project recipe. Swarm lanes report it instead of editing config.
