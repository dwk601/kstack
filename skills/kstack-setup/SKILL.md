---
name: kstack-setup
description: Configure role models, project checks and delivery recipes.
disable-model-invocation: true
---

# kstack-setup

Shared rules: read `../kstack/SKILL.md` first.

## User config

Config precedence: `$KSTACK_CONFIG`, `$XDG_CONFIG_HOME/kstack/config.json`, `~/.config/kstack/config.json`. See `references/config.example.json`.

- `models`: named presets: `cli`, exact `model`, `effort`, optional `args`. Built-ins: pi/codex/claude; Claude efforts: low/medium/high/xhigh/max.
- Custom: interactive `command`/noninteractive `oneshot` argv templates with `{model}`/`{effort}`, brief last. Flags in templates, not `args`; verify CLI --help. Optional `kind` overrides Herdr kind from command[0].
- `roles`: planner, plan_critic, workers, reviewer, verifiers, fixer. One preset each; verifiers also accepts a lane-rotated list, not a concurrency cap. CLIs may differ.
- `execution.max_fails`/`finish.max_fix_rounds`: positive nonboolean integers. `allow_merge`/`allow_deploy`: JSON booleans, default false. kstack-finish defines target/timeout.

1. `python3 scripts/kstack-models show`: user defaults, not project/request overrides. Missing config: use example, permissions false.
2. Discover Pi: `pi --list-models`; Codex: `model_catalog_json` in `~/.codex/config.toml` (otherwise ask); Claude/custom: CLI/docs. Validate effort support; model choices stay user-owned.
3. Preserve choices; change requested settings only; flag missing requirements. Show diff, write, run `python3 scripts/kstack-models validate --check`. Fix errors; warnings mean unverified availability (including Claude/custom models/flags). New agents only.

## Project config

Optional `.kstack/project.json`: `base`, `checks`, `verify`, `finish` overrides. Harness/map: `references/verify-harness.md`.

`finish.deployments` from real scripts/CI/docs:
- `name`, `paths`: component and affected paths; include shared/schema/config effects.
- `depends_on`, `environment`: prerequisites/destination.
- `mode`: `auto` or `manual`; `apply`: manual command or identified merge-triggered recipe.
- `verify`: delivered revision/environment evidence.

`finish.deploy_checks`: verification evidence fallback, not an apply recipe. Helper doesn't validate project recipes; kstack-finish preflight does before merge.
