---
name: kstack-setup
description: Configure role models, project checks and delivery recipes.
disable-model-invocation: true
---

# kstack-setup

Shared rules: read `../kstack/SKILL.md` first.

## User config

Resolve `$KSTACK_CONFIG`, then `$XDG_CONFIG_HOME/kstack/config.json`, then `~/.config/kstack/config.json`. See `references/config.example.json`.

- `models`: named presets with `cli`, exact `model`, `effort`, optional `args`. Built-ins: pi/codex/claude; Claude efforts: low/medium/high/xhigh/max.
- Custom presets: interactive `command` and noninteractive `oneshot` argv templates with `{model}`/`{effort}`, brief last. Put flags in templates, not `args`; verify CLI --help. Optional `kind` overrides Herdr kind from command[0].
- `roles`: planner, plan_critic, workers, reviewer, verifiers, fixer. Each names one preset; verifiers alone accepts a list, rotated across lanes, not a concurrency cap. Roles may use different CLIs.
- `execution.max_fails`/`finish.max_fix_rounds`: positive nonboolean integers. `allow_merge`/`allow_deploy`: JSON booleans, default false. kstack-finish defines target/timeout.

1. Run `python3 scripts/kstack-models show` for user defaults, not project/request overrides. Missing config starts from the example with permissions false.
2. Discover Pi via `pi --list-models`, Codex via `model_catalog_json` in `~/.codex/config.toml` (otherwise ask), Claude/custom via CLI/docs. Validate supported effort per model; keep model choices user-owned.
3. Change requested settings only; preserve choices on refresh and flag only missing required settings. Show diff, write, run `python3 scripts/kstack-models validate --check`. Fix errors; warnings leave availability unverified, including Claude/custom models/flags. Changes affect new agents.

## Project config

Optional `.kstack/project.json`: `base`, `checks`, real app-driving `verify`, `finish` overrides.

`finish.deployments` uses real scripts/CI/docs, not guesses:
- `name`, `paths`: component and affected paths; include shared/schema/config effects.
- `depends_on`, `environment`: prerequisites and destination.
- `mode`: `auto` or `manual`; `apply`: manual command or identified merge-triggered recipe.
- `verify`: delivered revision/environment evidence.

`finish.deploy_checks` is a verification evidence fallback, not an apply recipe. The helper does not validate project recipes; kstack-finish preflight does, before merge.

pr-green/`complete` select targets; reinstalling never overrides targets or user-owned permissions. Reinstall local edits with `npx skills add ./kstack`.
