---
name: kstack-improve
description: Prevent repeated mistakes with structure and checks.
disable-model-invocation: true
---

# kstack improve

Shared rules: read `../kstack/SKILL.md` first.

1. Find repeated classes in review FAILs, reverts, fixes, PR comments and user corrections. Require two occurrences.
2. Choose the highest effective level: structure (one state owner/task path; remove old way), types/lint naming the replacement (common patterns: fail only new uses), behavioral test, then AGENTS.md only for judgment calls.
3. Prove checks fail on real past mistakes and pass correct code.
4. Commit each class separately on assigned task branch, not unrelated feature work.

Report class, evidence, chosen level and why higher levels failed.
