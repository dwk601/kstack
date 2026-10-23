# Cleanup and local sync

For kstack-finish and shared temporary cleanup. Keep proofs in chat. Failed/uncertain checks mean retain and report partial; ownership alone is not integration/content safety.

## Ownership

Use creation/adoption inventory. Remote ownership needs job/remote/ref/SHA push proof or explicit adoption. Legacy needs prior proof or bounded user scope naming repo/resources/ownership, never Projects-wide.

Source deletion waits for confirmed merge and all target gates. Never delete base/shared/unmerged/unrelated resources. Recheck tips: delivery/integration/fix/follow-up needs verified PR-to-merge proof; workers need reviewed-tip ancestry in frozen delivery head and delivery-to-PR-to-merge chain. Squash/rebase needs API commit mapping. Renew after rewrites; retain advanced/unintegrated refs or unique commits. Detached verifiers must match recorded SHA.

Temporary cleanup never waits for merge: capture results, stop exact owned PIDs, remove safe scratch/disposable verifiers and read back absence on every settled return.

## Remote refs

Read `git ls-remote --heads <head-remote> refs/heads/<branch>`. Only successful empty output proves absence; skip absent refs, retain changed tips. Delete owned refs with:
`git push --force-with-lease=refs/heads/<branch>:<recorded-head> <head-remote> :refs/heads/<branch>`.
After failure reread: proven absent succeeds, else retain. Errors never prove absence; never retry unleased or with a new expected tip.

## Worktrees

Require clean, idle, unlocked, disposable worktrees without unique commits/writers. Check `git status --porcelain --untracked-files=all --ignored`: Git deletes ignored files; unknown/changed content blocks removal. Remove proven scratch, then recheck under quiescence.

Inspect every worktree including main; clean detached HEAD can hide paused rebase. Resolve `git -C <worktree> rev-parse --git-path <marker>` relative to that worktree and lstat: `rebase-merge`, `rebase-apply`, `BISECT_START`, `MERGE_HEAD`, `CHERRY_PICK_HEAD`, `REVERT_HEAD`, `sequencer`. Markers/symlinks/operations/uninspectable state retain worktrees and defer local ref deletion.

Move to a safe checkout; `git worktree remove <exact-path>` without force. Missing paths with metadata remain incomplete; never global prune. Never delete refs associated with `git worktree list --porcelain`.

## Temporary files

Require exact inventoried ephemeral type/hash; directories need unchanged entry sets/all hashes. Check containment and lstat every component: extra/changed entries, symlinks or ancestor escape block deletion. Recheck hashes immediately before unlink.

Inside repos, check every file with literal-pathspec `git ls-files --error-unmatch -- <relative-path>`: tracked forbids deletion; distinguish untracked from Git/path errors. Outside repos, require exact owned temporary root, not merely TMPDIR. Never patterns, git clean, broad prune/reset, forced worktrees or archive relocation.

## Local refs/config

Worktrees first. Prove `git branch -d` ancestry safety to fetched base and all operation-state checks. Squash/rebase needs exact API merge proof, unchanged tip and no commits beyond verified PR/worker chain. Never branch -D.

Keep inspection/deletion/config/readback quiescent. Match exact branch.<name> section to inventory snapshot, including duplicates/origins/scopes/file; not fresh observation/regex/prefix. CAS `git update-ref -d refs/heads/<branch> <expected-sha>` lacks branch safety; require the proofs above. Stale expected-old must reject; never retry a new tip. Failed CAS forbids config removal.

After successful CAS and ref-absence readback, recheck unchanged owned section, then `git config --file <owning-file> --remove-section branch.<name>`. Never unrelated/shared/unowned/global/included config. Changed/ambiguous config or lost quiescence means partial. Absent sections are idempotent after readback; absent refs with config need prior CAS proof.

Read back refs/paths/worktree metadata and exact config-section absence across origins/scopes, not just upstream keys. Path absence with metadata is not done. Record done/already absent/skipped with reason.

## Local sync

Fetch base remote; inspect surviving checkout's branch/status/operation markers. Fast-forward clean local base; rebase only explicitly owned local commits onto fetched base, never shared/published history or unrelated work. Preserve dirty/divergent unowned branches; no reset, automatic stash or forced switch. Conflicts block sync: preserve and report, never discard commits. Read back branch/HEAD/upstream/status; report delivery, cleanup and sync separately.
