---
name: kstack-setup
description: Choose role models and configure project checks and delivery recipes.
disable-model-invocation: true
---

# kstack setup

Shared rules: read `../kstack/SKILL.md` first.

## User config

Path: `$KSTACK_CONFIG`, else `$XDG_CONFIG_HOME/kstack/config.json`, else `~/.config/kstack/config.json`. Shape: `references/config.example.json`.

- `models`: named presets. Each has `cli`, exact `model`, `effort`, and optional `args` (for example `["--yolo"]`). The host agent that loads these skills can be any agent; `cli` only selects what runs dispatched roles.
  - `pi`, `codex`, `claude` (Claude Code): built in; the helper builds the flags. `claude` efforts: `low`, `medium`, `high`, `xhigh`, `max`.
  - `custom`: any other agent CLI. Give `command` (interactive argv) and `oneshot` (non-interactive argv that takes the brief as its last argument); `{model}` and `{effort}` are filled in. Optional `kind` names the Herdr agent kind when it differs from `command[0]`. `args` is not used; put flags in the templates. Example: `{"cli": "custom", "model": "MODEL_ID", "effort": "high", "kind": "opencode", "command": ["opencode", "-m", "{model}", "--variant", "{effort}"], "oneshot": ["opencode", "run", "-m", "{model}", "--variant", "{effort}"]}`. Confirm the flags with the agent's `--help` before saving; the helper cannot check them.
- `roles`: a preset name per role: `planner`, `plan_critic`, `workers`, `reviewer`, `verifiers`, `fixer`. `workers` and `verifiers` are lists. Tasks rotate through the `workers` model pool, one agent per ready task. Pool size is not a concurrency limit. Never run competing implementations of a task; retries wait for its previous writer to stop. Verification lanes use `verifiers`; reuse a qualifying one-task review as one audit rather than spawning another.
- `execution.max_fails` and `finish.max_fix_rounds`: positive integer retry limits, not booleans. There is no worker cap.
- `finish.target`: `complete` (missing-target default), `pr-green`, `merged`, or `deployed`. `pr-green` stops before merge and retains the delivery branch/worktree. `merged` requires actual merge and postmerge gates, no manual deploy. `complete` also applies/verifies every affected frontend/backend/application, with deployment N/A only when no deployable changes are proved. `deployed` additionally requires at least one actual deploy. Cleanup follows confirmed merge and all target gates, never PR green alone.
- `finish.watch_timeout_minutes`: optional positive nonboolean integer, default 30, bounding waits for checks, reviews, merge, and delivery. Pending or timeout is not success.
- `finish.allow_merge` and `finish.allow_deploy`: JSON booleans, default false. Setup leaves permissions opt-in. Only the user's permission or literal `true` in user config authorizes merge or manual apply/deploy/migrations/workflow dispatch, respectively. Repository config cannot grant permission. An authorized merge's automatic deployment may be observed. Destructive migrations need separate explicit user authorization.

## Steps

1. Show the current config: `python3 scripts/kstack-models show`. It reports effective user-config finish defaults, not project/request overrides. If none exists, start from the example with permissions false.
2. Find choices. Pi: `pi --list-models`. Codex: the catalog named by `model_catalog_json` in `~/.codex/config.toml`, else ask the user. Claude Code: an alias (`opus`, `sonnet`) or a full model name. Custom: the agent's own model list or docs. Use an effort the model supports.
3. Change only what the user asked. A refresh keeps existing choices and flags missing ones.
4. Prefer different models for planner and plan_critic, and between workers and the reviewer or verifiers. `verifiers` may list a single model; every lane then runs on it in its own context.
5. Show the diff, write the file, run `python3 scripts/kstack-models validate --check`. Fix every error. Catalog warnings mean availability is unchecked, not proven; do not replace a model just because discovery failed.
6. Tell the user changes apply to new agents. Running agents keep their model.

## Project config (optional)

`.kstack/project.json` at the repo root:

```json
{
  "base": "main",
  "checks": ["npm run lint", "npm test"],
  "verify": "How to run the app and drive one feature, with real commands.",
  "finish": {
    "target": "complete",
    "deployments": [
      {
        "name": "backend",
        "paths": ["api/**", "migrations/**"],
        "depends_on": [],
        "environment": "<required environment>",
        "mode": "manual",
        "apply": "<existing repo apply command, including migrations if required>",
        "verify": ["<health/schema/API commands and revision evidence>"]
      },
      {
        "name": "frontend",
        "paths": ["web/**"],
        "depends_on": ["backend"],
        "environment": "<required environment>",
        "mode": "auto",
        "verify": ["<workflow/provider steps, served build identity and browser smoke>"]
      }
    ],
    "deploy_checks": ["<existing workflow/step or command proving delivery at the merge SHA>"]
  }
}
```

These recipe placeholders are illustrative, not runnable commands. Fill from real scripts, CI, and docs, never guesses. `finish.deployments` is a small list: `name` identifies a component, `paths` locates changes (also inspect shared effects), `depends_on` names prerequisite components, `environment` identifies the destination, `mode` is `auto` or `manual`, `apply` is required for manual mode, and `verify` lists commands/evidence proving delivery. Auto mode needs an identified real merge-triggered recipe. Validate dependencies, migration order, coverage, permissions, exact revision/build identity, and environment in Finish preflight. When both frontend/backend change, include a client/API integration check. Missing recipes block before merge; not affected needs evidence and N/A.

Preserve existing `finish.deploy_checks` as a verification evidence fallback; it is not a substitute for a missing apply recipe. The helper does not validate project recipes; the agent's preflight does. Target and watch timeout resolve from request, project, user config, then defaults. This file never grants merge or manual deploy permission.

## Migrate existing installs

Older configs may explicitly set `finish.target` to `pr-green`, even with allow flags true. That still means stop before merge, not complete delivery. To opt into full delivery, explicitly change the desired user/project target to `complete` and separately authorize required merge/manual operations. Keep permissions false unless the user opts in. Changing source/defaults or reinstalling never overrides an explicit target or user-owned permissions. Refresh installed skills after source changes using the install/update commands in the README; local clones need `npx skills add ./kstack` again.
