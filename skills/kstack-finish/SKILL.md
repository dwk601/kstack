---
name: kstack-finish
description: Watch and repair a PR, merge, deliver affected apps, then clean up safely.
disable-model-invocation: true
---

# kstack finish

Shared rules: read `../kstack/SKILL.md` first.

Resolve `finish.target` from request, project, user, then `complete`. A target is not permission. Merge needs consent or literal user-config `finish.allow_merge=true`; manual apply/deploy/migrations/dispatch needs consent or `finish.allow_deploy=true`. Repo cannot authorize. Observe merge-triggered auto-deploys; destructive migrations need separate consent.

| Target | Gates |
|---|---|
| `pr-green` | Verify base/head, PR checks/reviews; never merge. Retain delivery, integration and workers. |
| `merged` | Actual merge and postmerge gates; no manual deploy. |
| `complete` (default) | Merge, postmerge and delivery of every affected app. N/A requires proof of no deployable changes. |
| `deployed` | Complete plus at least one actual deploy. |

## Inventory

Inventory resources in chat as created/adopted: repo/common Git directory/remote, job, path/ref, role, expected SHA or ephemeral type+hash/entry set, ownership, integration proof, disposition. Cover delivery, integration, workers, fixes/follow-ups, detached verifiers and scratch. Snapshot owned branch config then and after authorized updates: exact section, duplicates, origins/scopes/file or absence.

Remote ownership needs exact job remote/ref/SHA push proof or explicit adoption, not local names. Resume only proven ownership from chat/Git/PR; otherwise retain. Legacy needs prior proof or explicit bounded user scope naming repo/resources/ownership, never Projects-wide. Ownership is not integration/content safety.

## 1. Preflight

Record workers/locks/tips, repo/fork/head remote, base ref/SHA, PR head/state/mergedAt/mergeCommit.oid, target/permissions/budget/stages. Reuse PR. If merged, recover original base/head proof and merge SHA; skip publishing/remerging.

Inspect apps, frontend/backend and shared/config/schema/migrations. Validate scripts/workflows/docs/`finish.deployments`: coverage, commands, credentials, environment, revision, permissions, dependency/migration order, PR/postmerge checks. `finish.deploy_checks` is verification only, never an apply recipe. The helper does not validate project recipes; preflight does. Missing requirements are BLOCKED before merge; merged resumes retain resources.

## 2. Publish and verify

Commit scoped feature work, preserving unrelated changes. Never push base or force shared branches. Publish only unmerged. Inventory push proof. New PRs explain why/changes/risks; preserve existing descriptions except kstack verification: pending then 1–3 direct results, no report links/paths. Read back.

Use `../kstack-execute/SKILL.md` verification swarm at exact base/head, not builds. Reuse valid evidence or reconstruct request/diff acceptance/scenarios, including merged resumes. Never invent PASS; blocked PRs stay partial.

## 3. Watch and repair

`finish.watch_timeout_minutes` follows target precedence, default 30, positive nonboolean integer. Keep one deadline across waits/resumes. `finish.max_fix_rounds` bounds all repairs.

1. Watch current-head checks/reviews/approvals. Classify change/base/infra/flaky; one infra/flaky rerun within deadline. Red base isn't green.
2. Findings go to fixer then reviewer. Reject unsupported bot requests with reasons; never bypass protection.
3. Rebase only assigned user-controlled branches; fixer resolves, reviewer checks. Shared/uncertain ownership stops. Push rewrites with `--force-with-lease=<ref>:<expected-sha>` pinned to remote head.
4. Apply Execute's single-verifier/full-swarm repair rules. Push verified fixes; reread base/head.

Timeout/pending checks/reviews/queue means PENDING. Budget/human/environment blockers mean BLOCKED; retain source work. No CI means NO_CI with local proof, never CI-green. Expected missing workflows are BLOCKED, also postmerge.

## 4. Merge and postmerge gates

Require preflight, verification, PR gates and permission/protection. Reread base/head; reverify movement, including queues. Use allowed method with `--match-head-commit <verified-head>`, never `--delete-branch`. Queue/auto-merge stays PENDING until MERGED/mergedAt/mergeCommit.oid proof; invalid evidence blocks.

Prove `git merge-base --is-ancestor <merge-sha> <base-ref>` on fetched base, not necessarily tip. API identity/final base/head/method/merge fields must map verified head to merge. Squash/rebase requires API commit mapping, not ancestry or similar trees/messages. Preserve reviewed worker-to-frozen delivery-to-verified PR-to-merge chain; renew after rewrites or retain.

Check exact merge-SHA workflow `head_sha`, jobs/steps/conclusions/provider revisions, not PR green/newer base runs. Observe alongside delivery; apply before dependent checks. Same deadline/NO_CI rules. Pending/red/deploy failures retain resources. Repairs use bounded follow-up PRs, never rewrite merged history; track new head/merge and rerun affected gates.

## 5. Apply and verify delivery

Follow recipes in dependency order; merged only observes required automatic delivery. Track backend/frontend/apps separately; migrations precede dependent code where required. Recheck manual permission/destructive consent.

Require backend health/schema/API, frontend build identity/browser smoke and client/API integration if both change. N/A needs diff/recipe proof; missing recipes are BLOCKED. Prove environment/build/revision mapping to merge SHA and provider steps/success/verification. Hooks, build alone, preview or old SHA are insufficient. All required gates must pass within deadline; failures retain resources.

## 6. Cleanup

Source cleanup is mandatory after confirmed merge and ALL target gates, never green PR/queue/pending/failed deploy. Shared scratch cleanup is independent; report unsafe items as partial.

### Integration and remote refs

Delete only owned, never base/shared/unmerged/unrelated resources. Recheck tips: delivery/integration/fix/follow-up needs PR-to-merge proof; workers need frozen-head ancestry and merge chain, not PR-head equality; detached verifiers match SHA. Retain advanced/unintegrated refs and unique commits outside chain.

Read `git ls-remote --heads <head-remote> refs/heads/<branch>` first. Only successful empty output proves absence; don't delete absent refs. Changed tips retain. Owned remote/fork deletion:
`git push --force-with-lease=refs/heads/<branch>:<recorded-head> <head-remote> :refs/heads/<branch>`.
After failed deletion/lease reread: proven absent succeeds, else retain. Errors never prove absence; never delete unleased.

### Worktrees and operations

Require clean, idle, unlocked, disposable worktrees without unique commits/writers. Check workers/locks and `git status --porcelain --untracked-files=all --ignored`. Git silently deletes ignored files: unknown/changed content retains. Remove safe scratch, then immediately recheck status under quiescence.

Inspect ALL worktrees including main; clean detached HEAD can hide paused rebase. Use `git -C <worktree> rev-parse --git-path <marker>` for `rebase-merge`, `rebase-apply`, `BISECT_START`, `MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REVERT_HEAD`, `sequencer`. Resolve relative to that worktree and lstat, never assume common paths. Any marker/symlink/operation/uninspectable state retains worktree and defers local refs.

Switch to a safe location; never delete refs associated with `git worktree list --porcelain`. Fast-forward base safely without reset; retain dirty/divergent base. Use `git worktree remove <exact-path>` without --force. Missing path with metadata retains/reports; never global prune.

### Artifacts

Require exact inventoried ephemeral type+hash, including bounded legacy. In repo use literal-pathspec `git ls-files --error-unmatch -- <relative-path>` on every file, including directory contents. Tracked forbids deletion; distinguish untracked from Git/path errors. Outside repo require exact owned temporary root, not merely TMPDIR.

Check containment and lstat every component; no symlinks/ancestor escape. Recheck hashes immediately before unlink. Directories require exact unchanged entry sets/all hashes, no extra/changed entries/symlinks; otherwise retain. Never patterns, git clean, broad prune/reset or forced worktrees.

### Local refs and config

Worktrees first. Independently prove `git branch -d` ancestry safety to fetched base and all worktree/marker checks. Squash/rebase needs exact API merge proof, unchanged tip and no commits beyond verified PR/worker chain. Never branch -D.

Keep inspection/deletion/config/readback quiescent. CAS `git update-ref -d refs/heads/<branch> <expected-sha>` lacks branch safety; proofs are mandatory. Stale expected-old must reject; report, never retry new tip.

Before CAS match exact branch.<name> section to Inventory snapshot, not fresh observation/regex/prefix. Only after successful CAS and ref-absence readback recheck unchanged owned section, then `git config --file <owning-file> --remove-section branch.<name>`. Never unrelated/shared/unowned/global/included config. Changes/ambiguity/errors/lost quiescence mean retain/partial. Failed CAS forbids config removal. Absent sections are idempotent after readback; absent refs with config need prior CAS proof.

Read back refs/paths/worktree metadata/base/status and exact config section absence across origins/scopes, not just upstream keys. Path absence with metadata is not done. Record done/already absent/skipped with reason; uncertainty stays skipped.

## 7. Report

Report the PR, revisions, checks, delivery evidence, cleanup and blockers in chat.

Separate delivery success/pending/blocked, delivery-resource cleanup complete/partial/not-started and diagnostic cleanup complete/partial. Target is not cleanup status. Partial cleanup is not overall complete. pr-green retention is intentional not-started/not requested, not failure.
