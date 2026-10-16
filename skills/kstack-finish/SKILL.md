---
name: kstack-finish
description: Push the work, open or update its PR, and fix failures until checks are green. Use when the user invokes kstack-finish or asks kstack to ship.
disable-model-invocation: true
---

# kstack finish

Done means required checks are green on the PR's current head. Merge or deploy only when the target asks for it and the user allowed it (in the request, or `allow_merge` / `allow_deploy`).

## Publish

1. Find what to ship: the `kstack/<job>` branch, the current branch, or the PR the user named. Check the remote, base, fork or upstream, and any open PR. Reuse an open PR.
2. Read the full diff. Commit only in-scope changes; leave unrelated files alone. Never push to the base branch. Never force-push a shared branch.
3. Push. Open or update the PR: title in the repo's style, body with why, what changed, how it was verified, and risks. Read the PR back before reporting it.

## Watch and fix

Repeat up to `max_fix_rounds`:

1. Wait for checks on the current head SHA (`gh pr checks <pr> --watch`, or the forge's equivalent). A green run on an older SHA does not count.
2. If red, read the failed logs and classify: caused by this change, already broken on base, infrastructure, or flaky. Prove it, for example by checking the base branch's latest run. Infrastructure or flaky gets one rerun.
3. The `fixer` fixes real failures on this branch. The `reviewer` checks the fix with `../kstack-review/SKILL.md`. Push, then back to step 1.
4. Review comments: judge each against the code. Fix the real ones and reply to the rest with a reason. Do not change code just to quiet a bot.
5. Merge conflicts: rebase if the branch is yours and the resolution is clear. Otherwise stop and report.

Stop when green, when rounds run out, or when a human must decide. Never disable checks, skip tests, or change branch protection to get green. Report a failure that is already on base; do not hide it.

No CI: run the project checks locally and report `NO_CI` with that evidence.

## Merge and deploy (only when allowed)

Merge with the repo's method once approvals and protection allow it. Read back that it merged; a queued auto-merge is not merged. Then check `deploy_checks` from `.kstack/project.json` against the merge SHA by reading the actual step logs. Fix a broken deploy with a new PR, never by rewriting history.

## Report

PR URL, head SHA, check results, fixes made, what is still open. Keep local checks, CI, approvals, merge, and deploy as separate lines. Delete the branch only after it merged.
