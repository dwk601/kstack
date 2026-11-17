---
name: kstack-improve
description: Prevent recurring mistakes with structure and checks.
disable-model-invocation: true
---

# kstack-improve

Shared rules: read `../kstack/SKILL.md` first.

Agents copy the nearest example.

1. Evidence: recent commits/reverts, review comments/FAILs, user corrections, agent instruction files, workaround comments, kstack-improve candidates in reports. A class needs two occurrences; an unenforced AGENTS.md row's first new violation counts as the repeat.
2. In order: structure removing the old path (one owner, one supported way; delete copyable legacy) → types → lint/CI naming the replacement file/type/function in errors → behavioral tests → AGENTS.md prose only for judgment calls. Widespread patterns: fail new instances only.
3. One command, same locally/CI, in `.kstack/project.json` `checks`. Prove each fails on a real past mistake and passes correct code.
4. Exceptions only on the offending line: reason, expiry date, named human approver. Agent proposes, never self-approves.
5. AGENTS.md rule/enforcer table: only cross-session memory under no-saved-artifacts. Drop rules once their mistake cannot happen. Commit each class separately on its assigned branch.

Report each class, evidence, level and why not higher.
