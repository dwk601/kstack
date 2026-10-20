---
name: kstack-setup
description: Choose role models and configure project checks and delivery recipes.
disable-model-invocation: true
---

# kstack setup

Shared rules: read `../kstack/SKILL.md` first.

## User config

Use `$KSTACK_CONFIG`, else `$XDG_CONFIG_HOME/kstack/config.json`, else `~/.config/kstack/config.json`. Shape: `references/config.example.json`.

- `models` names presets: `cli`, exact `model`, `effort`, optional `args`. Built-ins are `pi`, `codex`, `claude`; helper builds flags. Claude efforts: low/medium/high/xhigh/max.
- Custom presets supply interactive `command` and noninteractive `oneshot` argv, brief last, with `{model}`/`{effort}` templates. Optional `kind` overrides Herdr kind from command[0]. Put flags in templates, not `args`; confirm with CLI --help.
- `roles`: planner, plan_critic, workers, reviewer, verifiers, fixer. Worker/verifier lists rotate tasks, not concurrency caps. Host CLI may differ.
- Retry limits `execution.max_fails`/`finish.max_fix_rounds` are positive nonboolean integers. Finish owns target/timeout; allow_merge/allow_deploy are JSON booleans, default false.

## Steps

1. `python3 scripts/kstack-models show` shows user defaults, not project/request overrides. If absent, use example with permissions false.
2. Discover Pi via `pi --list-models`; Codex via `model_catalog_json` in `~/.codex/config.toml`, else ask; Claude via alias/full name; custom via CLI/docs. Choose supported effort.
3. Change only requested settings; refresh preserves choices and flags missing ones. Prefer different planner/critic models.
4. Show diff, write, run `python3 scripts/kstack-models validate --check`, fix errors. Warnings mean unchecked availability; Claude/custom models/flags cannot be verified. Changes affect new agents only.

## Project config

Repo-root `.kstack/project.json` optionally sets `base`, `checks`, real app-driving `verify` and `finish` overrides. It cannot grant permission.

`finish.deployments` lists real scripts/CI/docs recipes, not guesses:

| Field | Meaning |
|---|---|
| `name` | Component |
| `paths` | Changed paths; also inspect shared/schema/config effects |
| `depends_on` | Prerequisites |
| `environment` | Destination |
| `mode` | `auto` or `manual` |
| `apply` | Manual command; auto needs identified merge-triggered recipe |
| `verify` | Exact delivered revision/environment evidence |

`finish.deploy_checks` is a verification evidence fallback, not an apply recipe. The helper does not validate project recipes; Finish preflight checks coverage, dependencies/migrations, permissions and revision/environment proof before merge.

## Existing installs

Explicit pr-green stops even with allow flags. Choose `complete` separately from permission. Defaults/reinstalling never overrides targets or user-owned permissions. Refresh via README; local clones need `npx skills add ./kstack`.
