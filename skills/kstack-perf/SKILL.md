---
name: kstack-perf
description: Measure bottlenecks and verify performance gains.
disable-model-invocation: true
---

# kstack-perf

Shared rules: read `../kstack/SKILL.md` first.

1. Set realistic workload/measurable target. Repeat a production-mode baseline; confirm correct output and actual work.
2. Locate limiter via profiler/trace; exclude profiling overhead from timings. Measurement-only and verification lanes stop short of edits.
3. Prefer skipping, reusing, reducing, deferring or batching work before parallelizing or speeding it up. Stop at target.
4. Alternate base/head runs: identical build mode/data/machine load. Without a base feature, use an absolute head budget. Noise is inconclusive, not speedup.

Report revisions, limiter evidence, before/after median/range, run count and delta. Explain the changed step's share of end-to-end time; gains cannot exceed it.
