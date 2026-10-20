# kstack

Explicit coding-agent skills for planning, reviewed implementation, verification and safe delivery. Inside [Herdr](https://herdr.dev), each role runs in its own pane with its chosen CLI/model. Outside Herdr, agents run sequentially in the foreground; missing agents leave verification gaps.

## Install and update

```sh
npx skills add dwk601/kstack
npx skills add dwk601/kstack -g --skill '*' -a claude-code -a codex -a pi -y
npx skills add ./kstack
npx skills update -g
npx skills list -g
```

Install all 11 skills together for sibling references. Requires Python 3; GitHub Finish uses `gh`. Local clones need `npx skills add ./kstack` after changes. Installs never touch user config. Changing defaults or reinstalling never overrides explicit targets or user-owned permissions. Existing pr-green installs still stop before merge; choose `complete` separately from granting permissions.

## Use

| Agent | Setup | Task | Ship |
|---|---|---|---|
| Claude Code | `/kstack-setup` | `/kstack <task>` | `/kstack-finish` |
| Codex | `$kstack-setup` | `$kstack <task>` | `$kstack-finish` |
| Pi | `/skill:kstack-setup` | `/skill:kstack <task>` | `/skill:kstack-finish` |

Other agents can be asked to use a skill by name. Entrypoints are explicit-only in frontmatter and `agents/openai.yaml`; agents ignoring both may still invoke them.

| Skill | Purpose |
|---|---|
| kstack | Route requests; shared rules |
| kstack-setup | Models, checks and delivery recipes |
| kstack-plan | Planner/critic cross-check |
| kstack-execute | Reviewed workers, serial integration, verification swarm |
| kstack-finish | Publish, watch/repair, merge, deliver and clean safely |
| kstack-understand | Explain code |
| kstack-debug | Runtime-backed diagnosis |
| kstack-review | Evidence-backed review |
| kstack-verify | Drive the real app at a known revision |
| kstack-perf | Measure bottlenecks and fixes |
| kstack-improve | Prevent repeated mistakes |

Tasks stop before publishing. Diagnosis/explanation are read-only; code changes use Plan and Execute. There is no test-first mandate or racing implementations.

## Configuration and delivery

Setup documents user config resolution (`$KSTACK_CONFIG`, XDG, then `~/.config/kstack/config.json`), presets and optional `.kstack/project.json`. See `skills/kstack-setup/references/config.example.json`. Built-in CLIs are Pi, Codex and Claude Code; custom presets provide interactive/oneshot argv templates. Roles may mix CLIs/models. Check custom flags against CLI help; helper validation cannot prove Claude/custom availability or project delivery recipes.

```sh
python3 skills/kstack-setup/scripts/kstack-models show
python3 skills/kstack-setup/scripts/kstack-models validate --check
```

[Shared rules](skills/kstack/SKILL.md) govern every skill. [Finish](skills/kstack-finish/SKILL.md) owns target precedence, permissions, delivery proof, ownership inventory and Git cleanup safeguards. Its default `complete` requires actual merge, postmerge gates and every affected application's delivery. pr-green never merges; merged omits manual deploy; deployed additionally needs an actual deploy. Missing permissions, recipes or evidence block; N/A requires proof. Repository settings cannot authorize operations. `finish.deploy_checks` supplies verification only, not an apply recipe; Finish validates real recipes before merge.

Results and ownership stay in conversation/stdout, never saved reports, plans, logs or state. Before every settled return, stop exact temporary processes, safely remove exact owned scratch/disposable verifiers and read back absence, even when blocked or pending. Preserve unmerged source work. No archive relocation or leftover logs-path footer. Source cleanup waits for merge and target gates, then requires ownership, integration, expected-SHA leases/CAS, worktree operation checks, exact unchanged config and path/content proofs. Unsafe cleanup is partial, not overall complete. Product files and authorized config/docs changes remain allowed.

## Tests

```sh
python3 -B -m unittest discover -s tests -v
```

Offline contracts and isolated Git sandboxes are not live proof of GitHub merging or deployment, nor an autonomous cleanup engine. Real Git tests use temporary repositories and a file:// remote, without network. Scratch uses nonempty TMPDIR or the platform fallback. Model discovery does not prove an end-to-end Herdr run.

## Credits

Adapted from [pstack](https://github.com/cursor/plugins/tree/850d7f2e9f5e55dff7eb00a0a479337fe79eb22f/pstack) by Lauren Tan (MIT). See `LICENSE`.
