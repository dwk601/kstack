# kstack

Explicit coding-agent skills for planning, reviewed implementation, verification and delivery. In [Herdr](https://herdr.dev), roles run in separate panes with chosen CLIs/models; elsewhere they run sequentially in the foreground. Missing agents leave verification gaps.

## Install

```sh
npx skills add dwk601/kstack
npx skills add dwk601/kstack -g --skill '*' -a claude-code -a codex -a pi -y
npx skills update -g
npx skills list -g
```

Install all 11 skills for sibling references. Requires Python 3; kstack-finish uses `gh` for GitHub. Reinstall local edits with `npx skills add ./kstack`. Installing never changes user config; reinstalling never overrides targets or user-owned permissions. Existing pr-green targets still stop before merge; choosing `complete` does not grant permission.

## Use

| Agent | Configure | Task | Ship |
|---|---|---|---|
| Claude Code | `/kstack-setup` | `/kstack <task>` | `/kstack-finish` |
| Codex | `$kstack-setup` | `$kstack <task>` | `$kstack-finish` |
| Pi | `/skill:kstack-setup` | `/skill:kstack <task>` | `/skill:kstack-finish` |

Other agents can use exact skill names. Frontmatter and `agents/openai.yaml` disable implicit invocation where supported.

| Skill | Purpose |
|---|---|
| [kstack](skills/kstack/SKILL.md) | Routing and shared rules |
| [kstack-setup](skills/kstack-setup/SKILL.md) | Role models, checks and delivery recipes |
| [kstack-plan](skills/kstack-plan/SKILL.md) | Code-grounded plan and independent critic |
| [kstack-execute](skills/kstack-execute/SKILL.md) | Reviewed implementation, integration and verification; no publishing |
| [kstack-finish](skills/kstack-finish/SKILL.md) | PR → fix red → green → merge → deploy → cleanup → local sync/rebase |
| [kstack-understand](skills/kstack-understand/SKILL.md) | Explain code |
| [kstack-debug](skills/kstack-debug/SKILL.md) | Runtime-backed diagnosis |
| [kstack-review](skills/kstack-review/SKILL.md) | Independent evidence-backed review |
| [kstack-verify](skills/kstack-verify/SKILL.md) | Exercise real behavior at known revisions |
| [kstack-perf](skills/kstack-perf/SKILL.md) | Measure bottlenecks and gains |
| [kstack-improve](skills/kstack-improve/SKILL.md) | Prevent recurring mistakes |

Diagnosis/explanation are read-only. Changes use kstack-plan → kstack-execute; shipping is a separate kstack-finish invocation.

## Configuration and safety

See [kstack-setup](skills/kstack-setup/SKILL.md) and its [config example](skills/kstack-setup/references/config.example.json). Built-in CLIs: Pi, Codex, Claude Code; custom presets supply argv templates. Model choices and permissions remain user-owned.

```sh
python3 skills/kstack-setup/scripts/kstack-models show
python3 skills/kstack-setup/scripts/kstack-models validate --check
```

kstack-finish defaults to `complete`: verified merge, postmerge gates and delivery of every affected app. Permissions, real recipes and evidence are required; missing requirements block. `finish.deploy_checks` verifies delivery but is not an apply recipe.

Results/inventory stay in chat/stdout, not saved run artifacts. Every settled return cleans safe owned temporary resources. Source cleanup waits for merge and target gates; unmerged/unrelated/uncertain work is preserved. [Cleanup safeguards](skills/kstack-finish/references/cleanup.md) cover ownership, leases, worktrees, files, config and local sync. Partial cleanup is not overall completion.

## Prompt design and tests

Skills use direct steps, explicit scope/completion, real checks and shared rules without repeated instructions. Based on Claude's [prompt overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview) and guides for [Fable 5.1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1), [Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) and [Sonnet 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5). These are prompt-design references, not model defaults.

```sh
python3 -B -m unittest discover -s tests -v
```

Tests cover naming/links, size budgets (including references), written safeguards, model commands and isolated Git semantics. They are not live proof of GitHub merging or deployment, model quality or an end-to-end Herdr run. Git sandboxes use temporary repositories and a file:// remote without network.

## Credits

Adapted from [pstack](https://github.com/cursor/plugins/tree/a66a8931c2dd71f1ed6abf6a52b1898a9f389ae4/pstack) by Lauren Tan (MIT). See `LICENSE`.
