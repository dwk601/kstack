# Verification harness

Interview the repo, not the user: surface; run; drive (existing harnesses first); observe; isolate.

`.kstack/project.json` `verify` commands: `launch`, `ready` (usable state, not an open port), `doctor` (read-only: is this instance ours and worth driving?), `teardown` (kill only what you started).

`.kstack/verify/`: driver recipe plus `features/`, one file per user-facing feature: sub-features, how to reach it (user POV), real commands/stable selectors, observable end state proving it, gotchas; optional `paths`. Only `verify.affected_only=true` opts into path narrowing.

Never weaken a journey to pass; missing precondition is a failure noted in gotchas.

Before handover prove launch → ready → doctor → drive one mapped feature → teardown; teardown after every failed attempt too.
