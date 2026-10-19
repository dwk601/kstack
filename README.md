# kstack

Agent skills for [Herdr](https://herdr.dev), the terminal workspace manager for AI coding agents. kstack turns Herdr into a team: it opens a pane per agent, starts the right agent in each (Claude Code, Codex, Pi, OpenCode, Gemini CLI, and more), briefs them, and collects their reports. Plan with two models that check each other, build the tasks with parallel reviewed workers, prove the result with a verification swarm, then push a PR and fix it until checks are green. Works in any repo.

The skills are plain `SKILL.md` files, so they install into any agent that the [`skills` CLI supports](https://github.com/vercel-labs/skills#supported-agents). Herdr is where they do their best work.

## Herdr

Run your agent inside a Herdr pane and kstack drives the rest:

- **Panes:** splits a sibling pane per agent (`herdr pane split`) and starts each role's agent there (`herdr agent start --kind <agent>`).
- **Briefs and reports:** sends each assignment with `herdr agent prompt` and collects results with `herdr agent read` and `herdr agent wait`. You can watch every agent work.
- **Mixed agents:** each role picks its own agent and model, for example Codex plans, Claude Code critiques, Pi builds. See [Config](#config).

Outside Herdr the skills still work, but one foreground agent at a time through one-shot commands: no parallel workers, and any missing agent leaves a verification gap. Presets map to Herdr agent kinds (`pi`, `claude`, `codex`); a `custom` preset sets `kind` to any other kind Herdr supports.

## Install

```sh
npx skills add dwk601/kstack            # pick agents interactively
npx skills add dwk601/kstack -g         # user-level, available in every project
npx skills add dwk601/kstack -g --skill '*' -a claude-code -a codex -a pi -y   # named agents, no prompts
npx skills add ./kstack                 # from a local clone
```

Install all 11 skills together; they reference each other by relative path. The CLI detects the agents you have installed; `-a <agent>` targets specific ones (names are in the supported-agents list above). Needs `python3` for model resolution and `gh` for Finish on GitHub.

## Update

```sh
npx skills update        # all installed skills; prompts for project or global
npx skills update -g     # global skills only
npx skills list -g       # what is installed, and for which agents
```

For a local clone, re-run `npx skills add ./kstack` after changes. Config in `~/.config/kstack/` is never touched by installs or updates.

## Use

Run setup once, then hand it a task.

| Agent | Setup | Task | Ship |
|---|---|---|---|
| Claude Code | `/kstack-setup` | `/kstack <task>` | `/kstack-finish` |
| Codex | `$kstack-setup` | `$kstack <task>` | `$kstack-finish` |
| Pi | `/skill:kstack-setup` | `/skill:kstack <task>` | `/skill:kstack-finish` |
| Any other agent | "use the kstack-setup skill" | "use the kstack skill to <task>" | "use the kstack-finish skill" |

- **Setup** picks the agent CLI, model, and effort per role.
- **Task** plans, then executes. It stops before publishing.
- **Ship** pushes, opens the PR, and fixes it until green.

All entry points are explicit-only, declared in the `SKILL.md` frontmatter (`disable-model-invocation`) and `agents/openai.yaml`. An agent that reads neither may still load them on its own. Invoked workflows read the supporting skills they need. Diagnosis and explanation stay read-only; code-changing requests use Plan and Execute.

## Skills

| Skill | Purpose |
|---|---|
| `kstack` | Entry point and shared rules |
| `kstack-setup` | Models per role, project commands |
| `kstack-plan` | Investigate; planner and critic cross-check a plan |
| `kstack-execute` | Parallel workers with per-task review, serial integration, then a verification swarm |
| `kstack-finish` | Push, PR, watch checks, fix until green |
| `kstack-understand` | How and why code works |
| `kstack-debug` | Root cause with runtime evidence |
| `kstack-review` | Plan, code, or audit review: PASS, FAIL, or BLOCKED with evidence |
| `kstack-verify` | Drive the real app and keep proof |
| `kstack-perf` | Baseline, limiter, measured fix |
| `kstack-improve` | Turn repeated mistakes into checks |

## Config

User config: `~/.config/kstack/config.json` (or `$KSTACK_CONFIG`). See `skills/kstack-setup/references/config.example.json`. Optional per-repo `.kstack/project.json` holds check commands and finish settings.

The agent you talk to can be any of the above. Each role (planner, critic, workers, reviewers, verifiers) runs through the CLI in its preset, so one job can mix agents:

| `cli` | Runs | Notes |
|---|---|---|
| `pi` | `pi --model <model>:<effort>` | Models from `pi --list-models` |
| `codex` | `codex -m <model> -c model_reasoning_effort=<effort>` | Catalog from `model_catalog_json` in `~/.codex/config.toml` |
| `claude` | `claude --model <model> --effort <effort>` | Alias (`opus`) or full name; efforts `low` to `max` |
| `custom` | Your `command` and `oneshot` argv templates | Any other agent CLI; `{model}` and `{effort}` are filled in |

A `custom` preset, for OpenCode as an example:

```json
"opencode": {
  "cli": "custom",
  "kind": "opencode",
  "model": "PROVIDER/MODEL_ID",
  "effort": "high",
  "command": ["opencode", "-m", "{model}", "--variant", "{effort}"],
  "oneshot": ["opencode", "run", "-m", "{model}", "--variant", "{effort}"]
}
```

Check the flags against the agent's `--help` first. The helper cannot verify `claude` or `custom` models; `validate --check` reports them as unchecked.

```sh
python3 skills/kstack-setup/scripts/kstack-models show
python3 skills/kstack-setup/scripts/kstack-models validate --check
python3 skills/kstack-setup/scripts/kstack-models cmd workers --index 2
python3 skills/kstack-setup/scripts/kstack-models cmd verifiers --index 1
```

## Checks

Run the offline helper tests from this repository:

```sh
python3 -B -m unittest discover -s tests -v
```

Catalog validation and skill discovery do not prove an end-to-end Herdr run.

## Not included

No test-first rule, no saved plan files, no racing several implementations of one task, no hidden background agents. Merge and deploy only when you allow them.

## Credits

Ideas adapted from [pstack](https://github.com/cursor/plugins/tree/850d7f2e9f5e55dff7eb00a0a479337fe79eb22f/pstack) by Lauren Tan (MIT). See `LICENSE`.
