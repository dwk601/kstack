---
name: kstack-setup
description: Choose the CLI, model, and effort kstack uses for each role, and record project commands. Use when the user invokes kstack-setup.
disable-model-invocation: true
---

# kstack setup

Shared rules: read `../kstack/SKILL.md` first.

## User config

Path: `$KSTACK_CONFIG`, else `$XDG_CONFIG_HOME/kstack/config.json`, else `~/.config/kstack/config.json`. Shape: `references/config.example.json`.

- `models`: named presets. Each has `cli` (`pi` or `codex`), exact `model`, `effort`, and optional `args` (for example `["--yolo"]`).
- `roles`: a preset name per role: `planner`, `plan_critic`, `workers`, `reviewer`, `security_reviewer`, `integration_reviewer`, `fixer`. `workers` is a list; tasks rotate through it, one task per worker, never the same task twice.
- `execution`: `max_workers` (concurrent tasks), `max_fails` (review FAILs before a task is blocked).
- `finish`: `target` (`pr-green`, `merged`, or `deployed`), `max_fix_rounds`, `allow_merge`, `allow_deploy`.

## Steps

1. Show the current config: `python3 scripts/kstack-models show`. If none exists, start from the example.
2. Find choices. Pi: `pi --list-models`. Codex: the catalog named by `model_catalog_json` in `~/.codex/config.toml`, else ask the user. Use an effort the model supports.
3. Change only what the user asked. A refresh keeps existing choices and flags missing ones.
4. Prefer different models for planner and plan_critic, and for workers and reviewer.
5. Show the diff, write the file, run `python3 scripts/kstack-models validate --check`. Fix every error.
6. Tell the user changes apply to new agents. Running agents keep their model.

## Project config (optional)

`.kstack/project.json` at the repo root:

```json
{
  "base": "main",
  "checks": ["npm run lint", "npm test"],
  "verify": "How to run the app and drive one feature, with real commands.",
  "finish": { "target": "pr-green", "deploy_checks": ["Workflow and step that prove the deploy"] }
}
```

Fill it from the repo's real scripts, CI, and docs, never from guesses. The finish target comes from the user's request, else this file, else user config. This file never grants merge or deploy; only `allow_merge`, `allow_deploy`, or the user does.
