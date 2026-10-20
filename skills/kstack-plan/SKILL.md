---
name: kstack-plan
description: Investigate and cross-check a temporary working plan.
disable-model-invocation: true
---

# kstack plan

Shared rules: read `../kstack/SKILL.md` first.

Keep a short code-grounded plan in conversation, never files.

1. Quote request and exclusions.
2. Planner investigates entrypoints, callers, data shapes, state and real checks. Use `../kstack-understand/SKILL.md` for unfamiliar code; identify affected data/state.
3. Define tasks: id, goal, observable acceptance, owned files, dependencies, check command. Parallel ownership is disjoint; keep coupled work together. One task is fine. List live scenarios/pass conditions and speed targets for Execute's swarm.
4. Independent critic checks against code once using `../kstack-review/SKILL.md` plan mode.
5. Planner applies valid points once. Resolve facts by reading/running code, not votes. Ask users only about product choices code cannot answer.
6. Return plan in chat; close only agents opened here.

Use configured `planner`/`plan_critic`. Coordinator may plan if its model matches `planner`; critic always needs a separate fresh context.
