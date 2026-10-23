---
name: kstack-plan
description: Build a code-grounded plan with an independent critic.
disable-model-invocation: true
---

# kstack-plan

Shared rules: read `../kstack/SKILL.md` first.

1. State request and exclusions. Configured `planner` traces affected code/data/state and available checks; use `../kstack-understand/SKILL.md` where unfamiliar.
2. Define tasks with goal, owned files, dependencies, observable acceptance and check command. Keep coupled work together; parallel ownership is disjoint. Include live scenarios/pass conditions and performance targets. One task is fine.
3. Fresh `plan_critic` checks once using `../kstack-review/SKILL.md` plan mode. Planner revises once; resolve facts with code, asking only unresolved product choices.

Return the plan in chat; close only agents opened here. Coordinator may plan when its model matches `planner`, never act as its own critic.
