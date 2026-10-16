---
name: kstack-improve
description: Prevent repeated mistakes with structure and checks.
disable-model-invocation: true
---

# kstack improve

Shared rules: read `../kstack/SKILL.md` first.

1. Collect evidence: recent review FAILs, reverts, fix commits, PR comments, and the user's corrections. A mistake class counts once it has happened twice.
2. Fix each class at the highest level that works:
   1. Structure: one owner for the state, one way to do the task, delete the old way.
   2. Types, or a lint rule whose error names the fix.
   3. A test of the behavior.
   4. A line in `AGENTS.md`, only for judgment calls.
3. Prove each new check fails on a real past mistake and passes on correct code.
4. Keep each class a separate commit in this improvement job, not unrelated feature work. Use the assigned task branch. Publish only through `kstack-finish`.

Report: each class, its evidence, the level chosen, and why a higher level did not work.
