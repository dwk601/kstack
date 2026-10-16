# kstack

Agent skills for coding with Pi and Codex. Plan with two models that check each other, execute as a reviewed swarm, then push a PR and fix it until checks are green. Works in any repo. Uses visible Herdr agents when run inside Herdr.

## Install

```sh
npx skills add <owner>/kstack        # from GitHub
npx skills add ./kstack              # from a local clone
```

Install all skills together; they reference each other by relative path. Needs `python3` for model resolution and `gh` for Finish on GitHub.

## Use

| Pi | Codex | Does |
|---|---|---|
| `/skill:kstack-setup` | `$kstack-setup` | Pick CLI, model, and effort per role. Run once. |
| `/skill:kstack <task>` | `$kstack <task>` | Plan, then execute. Stops before publishing. |
| `/skill:kstack-finish` | `$kstack-finish` | Push, open the PR, fix until green. |

All skills are explicit only. They never load on their own.

## Skills

| Skill | Purpose |
|---|---|
| `kstack` | Entry point and shared rules |
| `kstack-setup` | Models per role, project commands |
| `kstack-plan` | Investigate; planner and critic cross-check a plan |
| `kstack-execute` | Swarm: one worker and one reviewer per task, serial integration |
| `kstack-finish` | Push, PR, watch checks, fix until green |
| `kstack-understand` | How and why code works |
| `kstack-debug` | Root cause with runtime evidence |
| `kstack-review` | PASS, FAIL, or BLOCKED with evidence |
| `kstack-verify` | Drive the real app and keep proof |
| `kstack-perf` | Baseline, limiter, measured fix |
| `kstack-improve` | Turn repeated mistakes into checks |

## Config

User config: `~/.config/kstack/config.json` (or `$KSTACK_CONFIG`). See `skills/kstack-setup/references/config.example.json`. Optional per-repo `.kstack/project.json` holds check commands and finish settings.

```sh
python3 skills/kstack-setup/scripts/kstack-models show
python3 skills/kstack-setup/scripts/kstack-models validate --check
python3 skills/kstack-setup/scripts/kstack-models cmd workers --index 2
```

## Not included

No test-first rule, no saved plan files, no racing several implementations of one task, no hidden background agents. Merge and deploy only when you allow them.

## Credits

Ideas adapted from [pstack](https://github.com/cursor/plugins/tree/850d7f2e9f5e55dff7eb00a0a479337fe79eb22f/pstack) by Lauren Tan (MIT). See `LICENSE`.
