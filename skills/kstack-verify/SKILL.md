---
name: kstack-verify
description: Exercise real behavior and return revision-bound outcomes in chat.
disable-model-invocation: true
---

# kstack verify

Shared rules: read `../kstack/SKILL.md` first.

1. Pin the revision and scenario with a concrete pass condition. Find the run recipe in `.kstack/project.json`, docs, scripts, or CI. Prefer existing e2e tests, APIs, and CLI drivers.
2. Use an isolated checkout and instance with its own port, data, and test account. Wait until the scenario's first step succeeds, not merely until a port opens. Never touch production data or edit source as a verification lane.
3. Drive the scenario as a user would. Stream output and describe responses and side effects in chat. Avoid captures; if a real test/screenshot needs minimal data, keep it transient in exact job-owned TMPDIR scratch with ownership/type+hash recorded in conversation. Judge the stated pass condition, not whether the process started.
4. For base/head comparison, run comparable behavior on both. If base lacks the feature, record that fact and verify the added behavior and end state on head. Do not invent a baseline or a ratio between different workloads.
5. Before every settled return (PASS, FAIL, BLOCKED, pending, or handoff), stop only the processes you started, by exact PID first. Capture needed revision-bound outcomes in conversation, delete exact owned temporary captures/data and safe disposable verifier worktrees using shared/Finish safety rules, and read back absence. Never retain evidence files or relocate them to reports/cache/archive; unsafe removal means cleanup partial with the exact blocker in chat.

Return in stdout/chat `base/head SHAs | PASS/FAIL/BLOCKED | commands | observations | outcomes | diagnostic scratch cleanup`. Required behavior that cannot run, the wrong interaction method, or inconclusive evidence is BLOCKED. Use N/A only when a check genuinely does not apply, with a reason.

After a successful standalone run, offer to save a missing project recipe. Swarm lanes report it to the coordinator instead of editing project files.
