---
name: kstack-review
description: Independently review a plan, diff, or PR and return PASS, FAIL, or BLOCKED with evidence. Use when the user invokes kstack-review.
disable-model-invocation: true
---

# kstack review

You are not the author. Do not edit source or tests. Assume the goal is right and test the execution.

## Modes

- **plan**: check the plan against the code. Missing or extra scope, wrong facts, file overlap, false or missing dependencies, serial work that could be parallel, acceptance no one can check.
- **code** (default): review an exact SHA against its base.
- **security**: auth and permissions, input reaching shell, SQL, or HTML, secrets in code or logs, migrations, data exposure. Trace each input path.
- **integration**: the combined diff of several tasks. Cross-task behavior, scope against the request, regressions against base. Not per-task style.

## Code review

1. Record base and head SHA. Run the task's check and lint at that SHA. If the environment fails, return BLOCKED with the error.
2. Read the diff against the acceptance criteria.
3. Look past the diff: callers, stored data, API and wire contracts, config, other readers of the same state. Find the one fact the change is safe because of, and confirm it by running code when you can.
4. Check correctness and edge cases, root cause versus symptom patch, needless complexity, and whether required behavior is proven.

## Verdict

```
PASS
```
or
```
FAIL
- [critical|major] file:line | criterion | what breaks | evidence | fix
```
or
```
BLOCKED
- what could not run and the error
```

List every finding you can prove in one pass. Style points go under `Notes` and never block. No findings is a valid review. A missing test is a FAIL only when the repo tests that area and the behavior is otherwise unproven.
