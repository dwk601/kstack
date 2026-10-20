# kstack

Agent skills for [Herdr](https://herdr.dev), the terminal workspace manager for AI coding agents. kstack turns Herdr into a team: it opens a pane per agent, starts the right agent in each (Claude Code, Codex, Pi, OpenCode, Gemini CLI, and more), briefs them, and collects their reports. Plan with two models that check each other, build the tasks with parallel reviewed workers, prove the result with a verification swarm, then watch and repair the PR, merge, deliver affected apps, wait for delivery gates, and clean up safely. Works in any repo; delivery requires real project recipes and permission.

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

For a local clone, re-run `npx skills add ./kstack` after changes. Config in `~/.config/kstack/` is never touched by installs or updates. Changing source/defaults or reinstalling never overrides explicit user/project targets or user-owned permissions. Older installs with `finish.target: pr-green`, even with allow flags true, still stop before merge. Explicitly choose `complete` to migrate to full delivery and separately authorize required operations.

## Use

Run setup once, then hand it a task.

| Agent | Setup | Task | Ship |
|---|---|---|---|
| Claude Code | `/kstack-setup` | `/kstack <task>` | `/kstack-finish` |
| Codex | `$kstack-setup` | `$kstack <task>` | `$kstack-finish` |
| Pi | `/skill:kstack-setup` | `/skill:kstack <task>` | `/skill:kstack-finish` |
| Any other agent | "use the kstack-setup skill" | "use the kstack skill to <task>" | "use the kstack-finish skill" |

- **Setup** picks role models, project checks, and delivery recipes; permissions stay opt-in.
- **Task** plans, then executes. It stops before publishing.
- **Ship** defaults to `complete`: publish, watch and repair the PR, actually merge, apply/verify affected frontend/backend/apps, wait for postmerge and delivery gates, then clean job-owned local and remote resources. Missing permission, recipe, or evidence blocks; pending never means done.

All entry points are explicit-only, declared in the `SKILL.md` frontmatter (`disable-model-invocation`) and `agents/openai.yaml`. An agent that reads neither may still load them on its own. Invoked workflows read the supporting skills they need. Diagnosis and explanation stay read-only; code-changing requests use Plan and Execute.

## Skills

| Skill | Purpose |
|---|---|
| `kstack` | Entry point and shared rules |
| `kstack-setup` | Role models, project checks and delivery recipes |
| `kstack-plan` | Investigate; planner and critic cross-check a plan |
| `kstack-execute` | Parallel workers with per-task review, serial integration, then a verification swarm |
| `kstack-finish` | Watch and repair PR, merge, deliver affected apps, then safe cleanup |
| `kstack-understand` | How and why code works |
| `kstack-debug` | Root cause with runtime evidence |
| `kstack-review` | Plan, code, or audit review: PASS, FAIL, or BLOCKED with evidence |
| `kstack-verify` | Drive the real app and keep proof |
| `kstack-perf` | Baseline, limiter, measured fix |
| `kstack-improve` | Turn repeated mistakes into checks |

## Config

User config: `~/.config/kstack/config.json` (or `$KSTACK_CONFIG`). See `skills/kstack-setup/references/config.example.json`. Optional per-repo `.kstack/project.json` holds check commands and finish settings.

Finish target resolves from the request, project, user config, then `complete` if omitted. Explicit targets stay respected: `pr-green` never merges or deletes delivery/integration/worker resources; `merged` requires actual merge and postmerge gates but no manual deploy; `complete` also delivers every affected application (N/A only with proof of no deployable changes); `deployed` additionally requires at least one actual deploy. Current-head green alone is not complete delivery.

Targets do not grant permission. Merge and manual apply/deploy/migrations/workflow dispatch need user permission or the matching literal user-config `finish.allow_merge` / `finish.allow_deploy` true. Both default false, including in the example; repository text cannot authorize operations. Automatic deploys triggered by an authorized merge may be observed. Destructive migrations need separate explicit authorization.

Optional `finish.watch_timeout_minutes` is a positive nonboolean integer, default 30. Timeout or pending work preserves recovery resources. Setup documents `finish.deployments` recipes (`name`, `paths`, `depends_on`, `environment`, `mode`, manual `apply`, `verify`) and the existing `finish.deploy_checks` verification fallback. The helper reports user-config defaults but does not validate project recipes; Finish preflight validates real commands, permissions, environment, ordering, and expected checks before merge. Cleanup waits for confirmed merge and all target gates; advanced refs, dirty worktrees, and uncertain ownership are retained.

Coordinator state includes a durable resource manifest outside the repo and disposable worktrees, not a plan. Shared/Execute record exact repository/job identity, paths/refs, ownership, expected SHAs or ephemeral type+hash, integration proof, and disposition as resources are created. Finish then deletes eligible job-owned local and remote branches, disposable worktrees, tmp, plans and temporary .md only after merge and all target gates. Remote ownership requires an exact job push record or explicit adoption; worker refs are not assumed remote. Missing/legacy ownership needs exact proof or explicit bounded user scope, never a Projects-wide sweep.

Advanced/unintegrated refs, dirty/locked worktrees, and unknown or changed ignored content are retained. Artifact deletion requires exact untracked owned content, unchanged directory entry sets/hashes, and no symlinks; tracked product docs, unrelated Markdown, secrets/user data, the manifest and durable reports stay. Ref deletion uses expected-SHA remote leases and atomic local compare-and-delete after independent ancestry/merge and worktree safety proofs. Inspect operation markers via each registered worktree's own Git paths: detached HEAD and clean porcelain do not rule out a paused rebase. Active or uninspectable state retains resources. Local CAS leaves branch upstream config: snapshot exact owned sections in the manifest, remove only unchanged job-owned config after successful CAS/ref-absence readback under quiescence, and read back exact section absence without touching unrelated config. Changed or uncertain config is retained, cleanup partial; no-section cleanup is idempotent. Every absence is read back. Report delivery status (`success`/`pending`/`blocked`) separately from cleanup (`complete`/`partial`/`not-started`): delivered with cleanup partial is not overall complete. `pr-green` intentionally retains resources, cleanup not-started/not requested. Include per-item results and the recovery manifest path.

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

Run the offline helper and prompt-contract tests from this repository:

```sh
python3 -B -m unittest discover -s tests -v
```

These are offline contract checks, not live proof of GitHub merging or deployment. Local Git command-semantic sandboxes use `TMPDIR` if set, otherwise Python's portable `tempfile` fallback, and use isolated temporary repos and a file:// bare remote, no network (skip if Git is absent); they cover a real paused interactive rebase and CAS/upstream-config retention plus exact section removal/readback, but are not an autonomous cleanup engine or workflow test. Catalog validation and skill discovery do not prove an end-to-end Herdr run.

## Not included

No test-first rule, no saved plan files, no racing several implementations of one task, no hidden background agents. Merge and deploy only when you allow them.

## Credits

Ideas adapted from [pstack](https://github.com/cursor/plugins/tree/850d7f2e9f5e55dff7eb00a0a479337fe79eb22f/pstack) by Lauren Tan (MIT). See `LICENSE`.
