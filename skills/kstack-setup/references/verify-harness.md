# Verification harness

Interview repo, not user: surface, run, drive (existing harnesses first), observe, isolate.

`.kstack/project.json` `verify`: `launch`, `ready` (usable, not open port), `doctor` (read-only: ours/worth driving?), `teardown` (kill only what you started).

`.kstack/verify/`: driver recipe; `features/`, one file per user-facing feature: sub-features, user-POV entry points, real commands/stable selectors, observable end-state proof, gotchas; optional `paths`.

Never weaken journeys to pass; missing preconditions: BLOCKED, noted in gotchas.

Prove before handover: launch → ready → doctor → drive one mapped feature → teardown; teardown on all failures.
