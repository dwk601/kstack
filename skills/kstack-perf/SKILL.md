---
name: kstack-perf
description: Measure performance and improve it against a baseline.
disable-model-invocation: true
---

# kstack perf

Shared rules: read `../kstack/SKILL.md` first. Measurement-only and verification lanes never optimize or edit source.

1. State a measurable claim and realistic workload, e.g. export p50 under 200 ms on 60k rows.
2. Baseline repeated runs: median, range, errors; confirm work actually ran.
3. Find the limiter with profiler/trace, not code reading.
4. Try cheapest first: skip, avoid repetition, reduce, defer, batch, parallelize, then speed up. Stop at target.
5. Remeasure with identical build mode, data and machine load; alternate base/head. If base lacks feature, use an absolute head budget, never invented speedup. Differences within run noise are inconclusive.

Report before/after, delta, run count/range, limiter and revision-bound profiler/trace observations in chat, not artifact paths. Avoid saved profiles; unavoidable captures follow shared scratch cleanup.
