---
name: kstack-perf
description: Measure and fix a performance problem against a baseline. Use when the user invokes kstack-perf or a task is about speed or resources.
disable-model-invocation: true
---

# kstack perf

Shared rules: read `../kstack/SKILL.md` first.

1. Write the claim you want to make, for example "export p50 under 200 ms on 60k rows". Pick a realistic workload.
2. Baseline: run it several times and note median and range. Count errors and confirm the work actually ran.
3. Find the limiter with a profiler or trace, not by reading code.
4. Try the cheapest idea first: skip the work, avoid repeating it, do less, do it later, batch it, run it in parallel, then make it faster. Stop when the target is met.
5. Measure again the same way: same build mode, data, and machine load. A change inside the run-to-run noise is no change.

Report: before, after, delta, run count and range, the limiter, and the artifact path. Say inconclusive when it is.
