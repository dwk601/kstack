# Verification reuse

Before dispatch record lane, exact base/head, scope, commands, environment/toolchain, provenance and result in chat. Reuse only matching PASS or justified N/A. Unproven provenance or changed base/queue/head/commands/config/lockfile/toolchain/environment invalidates reuse; small repair/rebase heads keep only non-gate results the old→new diff provably cannot reach. Complete evidence needs zero new agents, worktrees or gates; otherwise run only missing lanes.

Task reviews (unreviewed work: one task) and the frozen-head audit use separate nonimplementers; neither replaces the other. One gate owner runs full required gates once per revision/environment; reviewers run focused probes, not duplicate suites.

Cap aggregate concurrency by available CPU/memory; sequence if unknown. Concurrent stateful lanes isolate checkouts/ports/data/builds.

Never reuse destructive-action safety checks; freshly recheck `cleanup.md`.
