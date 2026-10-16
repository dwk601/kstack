---
name: kstack-setup
description: Choose the agent CLI, model, and effort for each role.
disable-model-invocation: true
---

# kstack setup

Shared rules: read `../kstack/SKILL.md` first.

## User config

Path: `$KSTACK_CONFIG`, else `$XDG_CONFIG_HOME/kstack/config.json`, else `~/.config/kstack/config.json`. Shape: `references/config.example.json`.

- `models`: named presets. Each has `cli`, exact `model`, `effort`, and optional `args` (for example `["--yolo"]`). The host agent that loads these skills can be any agent; `cli` only selects what runs dispatched roles.
  - `pi`, `codex`, `claude` (Claude Code): built in; the helper builds the flags. `claude` efforts: `low`, `medium`, `high`, `xhigh`, `max`.
  - `custom`: any other agent CLI. Give `command` (interactive argv) and `oneshot` (non-interactive argv that takes the brief as its last argument); `{model}` and `{effort}` are filled in. Optional `kind` names the Herdr agent kind when it differs from `command[0]`. `args` is not used; put flags in the templates. Example: `{"cli": "custom", "model": "MODEL_ID", "effort": "high", "kind": "opencode", "command": ["opencode", "-m", "{model}", "--variant", "{effort}"], "oneshot": ["opencode", "run", "-m", "{model}", "--variant", "{effort}"]}`. Confirm the flags with the agent's `--help` before saving; the helper cannot check them.
- `roles`: a preset name per role: `planner`, `plan_critic`, `workers`, `reviewer`, `security_reviewer`, `verifiers`, `fixer`. `workers` and `verifiers` are lists. Tasks rotate through the `workers` model pool, one agent per ready task. Pool size is not a concurrency limit. Never run competing implementations of a task; retries wait for its previous writer to stop. Verification lanes use `verifiers`; reuse a qualifying one-task review as one audit rather than spawning another.
- `execution.max_fails` and `finish.max_fix_rounds`: positive integer retry limits, not booleans. There is no worker cap.
- `finish.target`: `pr-green`, `merged`, or `deployed`. `allow_merge` and `allow_deploy` are JSON booleans; omitted permissions mean false.

## Steps

1. Show the current config: `python3 scripts/kstack-models show`. If none exists, start from the example.
2. Find choices. Pi: `pi --list-models`. Codex: the catalog named by `model_catalog_json` in `~/.codex/config.toml`, else ask the user. Claude Code: an alias (`opus`, `sonnet`) or a full model name. Custom: the agent's own model list or docs. Use an effort the model supports.
3. Change only what the user asked. A refresh keeps existing choices and flags missing ones.
4. Prefer different models for planner and plan_critic, for the first two verifiers, and between workers and the reviewer or verifiers.
5. Show the diff, write the file, run `python3 scripts/kstack-models validate --check`. Fix every error. Catalog warnings mean availability is unchecked, not proven; do not replace a model just because discovery failed.
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
