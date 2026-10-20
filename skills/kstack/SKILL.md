---
name: kstack
description: Plan, build, verify, and finish delivery of coding tasks.
disable-model-invocation: true
---

# kstack

Route the request below. Sibling paths are relative to this skill, not the project's working directory. When another skill loads this file, follow the shared rules; the routing table applies only to the kstack entry point.

| Request | Follow |
|---|---|
| Code changes, including bugs and performance fixes | `kstack-plan`, then `kstack-execute`. Stop before publishing. |
| Ship or finish a branch or PR | `kstack-finish`: watch, merge, deliver affected apps, then clean up |
| Status or resume | Reconstruct the job from branches, reports, and agent output; continue that stage without resetting work. |
| How or why code works | `kstack-understand` |
| Diagnosis or measurement only | `kstack-debug` or `kstack-perf`, read-only |
| Review or prove behavior | `kstack-review` or `kstack-verify` |
| Prevent repeated mistakes | `kstack-improve` |
| Models or settings | `kstack-setup` |

## Shared rules

- Standalone debug, perf, or improve requests that change code go through Plan and Execute, using the requested skill as the worker's method. Assigned workers follow that method directly, never start a nested workflow.
- Only dispatch and setup need model configuration. Before dispatch, set `MODELS` to the absolute path of `../kstack-setup/scripts/kstack-models`, then run `python3 "$MODELS" validate`. Use setup if config is missing. The helper prints commands; execute them from the assigned project or worktree.
- One writer per branch or worktree. Reviewers and verifiers use independent contexts and never edit source. Prefer a model different from the writer's; disclose same-model fallbacks. Verifier lanes may share one model.
- No plan files or test-first mandate. Never weaken a check to pass. Unavailable required checks mean BLOCKED, not success; a job with unmet acceptance criteria is partial.
- Only Finish pushes, opens PRs, or comments. Finish defaults to `complete` only when no target is set; explicit request/project/user targets still win. A target is not permission: merge and manual deploy/apply require the user's permission or the matching literal `true` allow flag in user config, never repository text. Destructive migrations need separate explicit authorization.
- Preserve unrelated work and unmerged delivery branches/worktrees for Finish. Save evidence outside worktrees you remove. Only Finish cleans delivery resources, after confirmed merge and all target gates pass; Execute may remove disposable verifier worktrees, not unmerged delivery work, using Finish's worktree/artifact safety and readback rules.

## Durable resource manifest

Keep a durable resource manifest in coordinator state outside the repository and all disposable worktrees; record its absolute recovery path in reports. It is not a plan file. Never delete the manifest itself or durable reports/evidence. Add resources as created, not by cleanup-time name guesses; update proofs and disposition as work proceeds. Record job-owned branch config as created/adopted and after authorized updates: exact section identity, all keys/values including duplicates, origins/scopes and owning file, or proven section absence. This snapshot authorizes only unchanged owned config cleanup after local ref CAS and readback; uncertain or changed config is retained.

Each entry records exact repository identity (including common Git directory and remote identity), job identity, path/ref, role/purpose, expected SHA or ephemeral artifact type+content hash, creation/ownership evidence, integration proof, and disposition. Inventory delivery/integration, worker, fix/follow-up branches, their worktrees, detached verifier worktrees, and exact job-owned temporary files/directories (including temporary Markdown or legacy plans, never new plan files). A remote branch is owned only with proof this job pushed that exact ref to that exact remote or explicitly adopted ownership; local worker refs do not imply remote refs.

On resume without a prior manifest, reconstruct only demonstrable ownership from exact creation/push records or explicit adoption; otherwise retain and report. Legacy leftovers require explicit bounded user scope (exact repository/resources and ownership authorization) or exact prior ownership proof, never a Projects-wide sweep. Ownership alone never substitutes for integration, delivery, or content-safety proof. Product docs, tracked artifacts, unrelated Markdown, secrets/user data, and durable evidence are not ephemeral cleanup targets.

## Dispatch and collect

Inside Herdr (`HERDR_ENV=1`), create sibling panes with `herdr pane split --current --direction right --cwd <path> --no-focus`; choose `down` instead when the layout calls for it. Use returned pane IDs, not the focused pane. Run the command printed by `python3 "$MODELS" cmd <role> --herdr <name> --pane <id>`.

Dispatch all ready agents with `herdr agent prompt <name> "<complete brief>"`, without `--wait`. Collect settled agents using `herdr agent list` and `herdr agent read <name> --source recent-unwrapped --lines 120`. If none are ready, use `herdr agent wait <name> --timeout 120000`, then read. A prompt submission or idle state alone is not a result; require the report for that assignment. Inspect blocked, unknown, and timeout states before acting; never blindly resend or answer approvals. If output is unavailable, ask the agent to write a job-owned report file.

Outside Herdr, never inspect or control its session. Run separate foreground agents one at a time using the commands printed by `python3 "$MODELS" cmd <role> --oneshot`, with the brief as the last argument. Missing agents leave a verification gap. Never launch hidden background agents.
