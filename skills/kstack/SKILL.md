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
| Status or resume | Reconstruct the job from this conversation, agent stdout, and actual Git/PR state; continue that stage without resetting work, never requiring saved logs. |
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
- Preserve unrelated work and unmerged delivery branches/worktrees for Finish. Capture needed outcomes in conversation before removing scratch. Only Finish cleans delivery resources, after confirmed merge and all target gates pass; Execute may remove disposable verifier worktrees, not unmerged delivery work, using Finish's worktree/artifact safety and readback rules.

## No saved run artifacts — all 11 skills

Return all reports and final results in stdout/chat. Keep run inventory, state, notes, plans, and evidence only in the current conversation/memory, never in files inside or outside the repo. No stage creates logs, notes, reports, plans, manifests, state files, or other persistent run output files. Stream subprocess output and summarize commands, exact revisions, observations, and outcomes in chat; never redirect/tee it into saved logs. Do not relocate artifacts to reports, cache, or archive directories. User-requested product files and authorized config/docs changes are not run artifacts; leave existing application logs, config, docs, and user data untouched unless explicitly in scope.

Avoid diagnostic files. If real tests/screenshots require minimal temporary captures or data, use exact job-owned scratch under `TMPDIR` (unset/empty uses the platform temporary-directory fallback). Record exact paths, ownership and type+hash/entry sets in conversation as created. Before every settled return, including success, failure, blocked, pending, timeout, `pr-green`, and Execute handoff: stop temporary processes you started by exact PID first, capture needed results in conversation, then safely delete only exact owned scratch paths and read back absence using Finish's artifact safety rules. Clean disposable verifier worktrees using its worktree safety rules too. This diagnostic scratch cleanup is not gated on merge or delivery. Unmerged source branches/worktrees and unique code are recovery resources, not disposable diagnostic scratch; preserve them on failures. If deletion cannot safely complete, report cleanup partial with the exact blocker in chat, never false complete. Never print a leftover logs-path footer or move leftovers elsewhere.

## In-conversation resource inventory

Keep the resource inventory only in the current conversation/memory, not a file or external durable store. Add resources as created, not by cleanup-time name guesses; update proofs and disposition as work proceeds. Record job-owned branch config as created/adopted and after authorized updates: exact section identity, all keys/values including duplicates, origins/scopes and owning file, or proven section absence. This snapshot authorizes only unchanged owned config cleanup after local ref CAS and readback; uncertain or changed config is retained.

Each entry records exact repository identity (including common Git directory and remote identity), job identity, path/ref, role/purpose, expected SHA or ephemeral artifact type+content hash, creation/ownership evidence, integration proof, and disposition. Inventory delivery/integration, worker, fix/follow-up branches, their worktrees, detached verifier worktrees, and exact job-owned temporary files/directories (including temporary Markdown or legacy plans, never new plan files). A remote branch is owned only with proof this job pushed that exact ref to that exact remote or explicitly adopted ownership; local worker refs do not imply remote refs.

On resume without a prior in-conversation inventory, reconstruct only demonstrable ownership from conversation plus actual Git/PR state and exact creation/push records or explicit adoption; otherwise retain and report. No saved logs are needed. Legacy leftovers require explicit bounded user scope (exact repository/resources and ownership authorization) or exact prior ownership proof, never a Projects-wide sweep. Ownership alone never substitutes for integration, delivery, or content-safety proof. Product docs, tracked artifacts, unrelated Markdown, existing application logs/config and secrets/user data are not ephemeral cleanup targets.

## Dispatch and collect

Inside Herdr (`HERDR_ENV=1`), create sibling panes with `herdr pane split --current --direction right --cwd <path> --no-focus`; choose `down` instead when the layout calls for it. Use returned pane IDs, not the focused pane. Run the command printed by `python3 "$MODELS" cmd <role> --herdr <name> --pane <id>`.

Dispatch all ready agents with `herdr agent prompt <name> "<complete brief>"`, without `--wait`. Collect settled agents using `herdr agent list` and `herdr agent read <name> --source recent-unwrapped --lines 120`. If none are ready, use `herdr agent wait <name> --timeout 120000`, then read. A prompt submission or idle state alone is not a result; require the report for that assignment. Inspect blocked, unknown, and timeout states before acting; never blindly resend or answer approvals. Agents return final results in stdout, never report files. If output is unavailable, inspect the agent's status and retry stdout collection or request a stdout summary; if still unavailable, record a verification gap, never ask for a saved report.

Outside Herdr, never inspect or control its session. Run separate foreground agents one at a time using the commands printed by `python3 "$MODELS" cmd <role> --oneshot`, with the brief as the last argument. Missing agents leave a verification gap. Never launch hidden background agents.
