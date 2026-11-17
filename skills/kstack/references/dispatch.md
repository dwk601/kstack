# Dispatch

MODELS: absolute `../../kstack-setup/scripts/kstack-models`. Run `python3 "$MODELS" validate`; missing: kstack-setup. Run printed commands in assigned checkouts.

Start every brief: role; read `<absolute path to kstack/SKILL.md>` shared rules first. Acceptance + checks are the whole bar; request stdout `task | SHA | files | checks + results | assumptions`.

Herdr (`HERDR_ENV=1`):
1. `herdr pane split --current --direction right --cwd <path> --no-focus`.
2. `python3 "$MODELS" cmd <role> --herdr <name> --pane <returned-id>`.
3. `herdr agent prompt <name> "<brief>"`, no --wait; work independently.
4. `herdr agent list`; `herdr agent read <name> --source recent-unwrapped --lines 120`. None ready: `herdr agent wait <name> --timeout 120000`, then read.

Require assignment stdout, not idle/submission. Inspect blockers/timeouts; retry collection, not resends/approvals. Missing results are verification gaps, never report files.

Outside Herdr leave its sessions alone; run foreground agents sequentially: `python3 "$MODELS" cmd <role> --oneshot`, brief last; no hidden background agents.
