# Cleanup and local sync

Failed/uncertain checks mean retain and report partial; ownership alone is not integration/content safety.

## Ownership

Use creation/adoption inventory. Remote ownership needs job/remote/ref/SHA push proof or explicit adoption. Legacy needs prior proof or bounded user scope naming repo/resources/ownership, never Projects-wide.

Source deletion waits for confirmed merge and all target gates. Never delete base/shared/unmerged/unrelated resources. Recheck tips: delivery/integration/fix/follow-up needs verified PR-to-merge proof; workers need reviewed-tip ancestry in frozen delivery head and delivery-to-PR-to-merge chain. Squash/rebase needs API commit mapping. Renew after rewrites; retain advanced/unintegrated refs or unique commits. Detached verifiers must match recorded SHA.

## Calls

Use `scripts/kstack-git` from finish; other skills use `../kstack-finish/scripts/kstack-git`. Use `--help` for arguments. At creation record `kstack-git snapshot-branch-config` digest in chat.

Quiesce writers; use inventory proofs, never a newly observed tip:
1. `kstack-git scratch-digest`, then `kstack-git delete-scratch` for exact owned scratch on every return.
2. `kstack-git delete-remote-branch` after source gates.
3. `kstack-git remove-worktree` for disposable worktrees.
4. `kstack-git delete-local-branch` with recorded config digest.
5. `kstack-git sync-local` last.

Only done/absent counts as cleaned. Report delivery, cleanup and sync separately; retained/error is partial.
