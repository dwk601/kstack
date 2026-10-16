---
name: kstack-plan
description: Investigate a coding task and build a working plan that two models cross-check. Use when the user invokes kstack-plan or kstack starts a task.
disable-model-invocation: true
---

# kstack plan

Shared rules: read `../kstack/SKILL.md` first.

Goal: a short plan grounded in the code. It stays in the conversation. Do not write plan files.

1. Quote the request. Note what is out of scope.
2. Planner investigates: entry points, callers, data shapes, state, and the repo's real check commands. Use `../kstack-understand/SKILL.md` for unfamiliar code. Name the data shape or state the change touches.
3. Planner splits the work into tasks. Each task: id, goal, observable acceptance criteria, owned files, depends-on, risk, check command. Risk is high only for auth, permissions, migrations, secrets, payments, or data loss. Parallel tasks own disjoint files. Keep coupled work in one task. One task is fine. Also list what proves the job: the user-visible behaviors to check live and any speed target. Execute's verification swarm runs from this list.
4. Plan critic checks the plan once, independently, against the code, using `../kstack-review/SKILL.md` in plan mode.
5. Planner applies the valid points once. Settle factual disagreements by reading or running code, not by vote. Ask the user only for a product choice the code cannot answer.
6. Return the final plan in chat. Close only agents this stage opened.

Roles: `planner` and `plan_critic` from config. If the coordinator's own model matches `planner`, it may plan itself. The critic is always a separate agent with a fresh context.
