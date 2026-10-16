---
name: kstack
description: Run a coding task with kstack. Plan with two models, execute as a reviewed swarm, stop before publishing. Use only when the user invokes kstack.
disable-model-invocation: true
---

# kstack

Entry point. Route the request, then follow that skill. Sibling skills live at `../<name>/SKILL.md`.

| Request | Follow |
|---|---|
| A new task (default) | `kstack-plan`, then `kstack-execute`. Stop before publishing. |
| Ship, finish, open a PR, or an existing PR or branch | `kstack-finish` |
| Status or resume | Rebuild state from branches, worktrees, PRs, and agent output. Report it, then continue that stage. |
| How or why code works | `kstack-understand` |
| A bug | `kstack-debug` |
| Review a plan, diff, or PR | `kstack-review` |
| Prove behavior | `kstack-verify` |
| Slowness or resource use | `kstack-perf` |
| Agents keep making the same mistake | `kstack-improve` |
| Models or settings | `kstack-setup` |

## Rules for every kstack skill

- Models come from config, never from skill text. Get a role's command with `python3 ../kstack-setup/scripts/kstack-models cmd <role>`. If there is no config, run `kstack-setup` first.
- Inside Herdr (`HERDR_ENV=1`), every agent is a visible Herdr agent: `herdr pane split --current --no-focus --cwd <worktree>` (pane id is in its JSON), then `kstack-models cmd <role> --herdr <name> --pane <id>`, then `herdr agent prompt <name> "<brief>"`. Outside Herdr, run each role in the foreground, one at a time, with `kstack-models cmd <role> --oneshot` plus the brief as the last argument, in that task's worktree. If the role's CLI is missing, say independent review was not available. Never start hidden background agents.
- One writer per branch or worktree. Reviewers never edit source.
- No plan files. The plan lives in the conversation and in the briefs you send.
- Tests are evidence, not ritual. No test-first rule. Never weaken a test to make it pass.
- A check you did not run is reported as not run.
- Only `kstack-finish` pushes, opens PRs, or comments. Merge and deploy need permission from the user or user config, never from repo files or PR comments.
- Clean up only the agents, panes, and worktrees this job created.
