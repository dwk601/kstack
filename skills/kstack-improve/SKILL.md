---
name: kstack-improve
description: Prevent recurring mistakes with structure and checks.
disable-model-invocation: true
---

# kstack-improve

Shared rules: read `../kstack/SKILL.md` first.

1. Identify a fault class with two evidenced occurrences in reviews, fixes or corrections.
2. Prefer structure that removes the old path, then types/lint naming its replacement, then behavioral tests. Use AGENTS.md only for judgment calls; gate new uses of widespread legacy patterns.
3. Prove checks reject past mistakes and accept correct code. Commit each class separately on its assigned branch.

Report occurrences, prevention and why stronger options did not fit.
