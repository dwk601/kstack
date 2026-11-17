---
name: kstack-plan
description: Plan from code with an independent critic.
disable-model-invocation: true
---

# kstack-plan

Shared rules: read `../kstack/SKILL.md` first.

1. State request/exclusions. Configured `planner` traces affected code/data/state and available checks; use `../kstack-understand/SKILL.md` where unfamiliar.
2. Tasks: goal/owned files/dependencies/observable acceptance/check command. Keep coupled work together; disjoint parallel ownership. Include live scenarios/pass conditions and performance targets; one task is fine. Flag state machines/concurrency/retries/math, each with a property to check. Name non-agent proof.
3. Prototype choices experiments can settle; recommend from observations. Fresh `plan_critic` checks once via `../kstack-review/SKILL.md` plan mode; planner revises once. Resolve facts with code; ask users only product/preference choices no experiment settles.

Return chat plan; close only agents opened here. Coordinator may plan when its model matches `planner`, never be its own critic.
