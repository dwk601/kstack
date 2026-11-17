---
name: kstack-improve
description: Prevent repeats with structure and checks.
disable-model-invocation: true
---

# kstack-improve

Shared rules: read `../kstack/SKILL.md` first.

Agents copy the nearest example.

1. Evidence: recent commits/reverts, review comments/FAILs, user corrections, agent instruction files, workaround comments, reports' kstack-improve candidates. Class: two occurrences; an unenforced AGENTS.md rule's first new violation counts as repeat.
2. In order: remove old paths structurally (one owner/one supported way; delete copyable legacy) → types → lint/CI errors naming replacement file/type/function → behavioral tests → AGENTS.md prose only for judgment calls. Widespread patterns: fail new instances only.
3. One identical local/CI command in `.kstack/project.json` `checks`. Prove each fails on a real past mistake and passes correct code.
4. Exceptions only on the offending line: reason, expiry date, named human approver. Agent proposes, never self-approves.
5. AGENTS.md rule/enforcer table: only cross-session memory under no-saved-artifacts. Drop rules whose mistake cannot happen. Commit each class separately on its assigned branch.

Report each class, evidence, level and why not higher.
