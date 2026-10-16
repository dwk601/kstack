---
name: kstack-finish
description: Push a PR and fix it until verified and CI-green.
disable-model-invocation: true
---

# kstack finish

Shared rules: read `../kstack/SKILL.md` first.

Resolve the target from the request, project config, then user config. Success requires verification of the current head and green required CI. Merge and deploy are separate, explicitly authorized targets.

## Publish

1. Identify the branch or existing PR, remote, base, and fork/upstream. Reuse its PR. No previous kstack session is required.
2. Commit only in-scope changes on a feature branch; leave unrelated files alone. Never push to the base branch or force-push a shared branch.
3. Push and open/update the PR. New PRs get a short why/changes/risks summary. Preserve an existing author's description; edit only a kstack verification section. Mark it pending until results exist, then use one to three outcome bullets after verification or repairs. Full tables stay in the job report; link only shareable evidence and read updates back.
4. Establish evidence for its current base/head pair using Execute's verification swarm section (`../kstack-execute/SKILL.md`). Reuse valid existing results. If none exist, reconstruct the acceptance/scenarios from the request and diff and run the swarm, not the build stages. A blocked run may leave a clearly marked partial PR, never a success claim.

## Watch and fix

Watch checks and review feedback on the current head (`gh pr checks <pr> --watch`, or equivalent). Allow at most `finish.max_fix_rounds` repair rounds, including repairs requested by verification.

1. Read failures and classify them with evidence: this change, already failing on base, infrastructure, or flaky. Infrastructure/flaky failures get one rerun. A red base is still reported, not hidden or called green.
2. Send real CI, review, or verification findings to the `fixer`. The `reviewer` checks each resulting diff. Do not change code merely to quiet a bot; reply to rejected findings with a reason.
3. For a necessary rebase on a user-controlled branch assigned to this job, let the fixer resolve conflicts and have the reviewer check them. On a shared branch or uncertain ownership, stop with conflict details rather than rewrite history. Push rewritten history only with `--force-with-lease=<ref>:<expected-sha>` pinned to the previously observed remote head.
4. After every fix or rebase, use Execute's single-verifier rule on the new head: inspect the diff, run gates and affected scenarios. New behavior or a large diff repeats the full swarm. Review alone does not carry old behavioral evidence forward.
5. Push verified fixes, then watch their CI and feedback again. Re-read the PR head before accepting any result; older green runs do not count.

Stop when verified and green, the repair budget is spent, or a human/environment blocker remains. Never disable checks, weaken tests, or alter protection to obtain green. No CI means report `NO_CI` with local evidence, not CI-green.

## Merge and deploy

Only proceed when the requested target and permissions allow it, approvals/protection permit it, and no required evidence is missing. Recheck the remote head and base; a change affecting the patch needs re-verification. Merge using the repo's method, then read back the merge SHA. A queued auto-merge is not a merge.

For a deployed target, verify the configured deployment steps at the merge SHA from actual logs. Missing deployment evidence is BLOCKED. A broken deploy needs a new fix PR within the remaining repair budget, never rewritten history. A merged target does not authorize a manual deploy.

## Report

PR URL, verified head, CI results, open findings, and the requested target's outcome. Keep verification, CI, approvals, merge, and deploy distinct. Delete only job-owned branches after a confirmed merge; retain evidence.
