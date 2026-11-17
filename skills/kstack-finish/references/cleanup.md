# Cleanup

Failed/uncertain checks: retain/report partial; ownership alone is not integration/content safety.

Use creation/adoption inventory. Remote ownership: job/remote/ref/SHA push proof or explicit adoption. Legacy: prior proof or user-bounded scope naming repo/resources/ownership, never Projects-wide.

Source deletion needs confirmed merge + all target gates. Never delete base/shared/unmerged/unrelated resources. Recheck tips: delivery/integration/fix/follow-up needs verified PR→merge proof; workers need reviewed-tip ancestry in frozen delivery head; `--via-head SHA --pr N` requires PR MERGED, head=SHA, merge on fetched base. Squash/rebase needs API commit mapping. Renew after rewrites; retain advanced/unintegrated refs/unique commits. Detached verifiers must match recorded SHA.

## Calls

Use `scripts/kstack-git` (siblings: `../kstack-finish/scripts/kstack-git`; `--help`). Record `kstack-git snapshot-branch-config` digest in chat at creation.

Canonicalize via realpath. Quiesce writers; use inventory proofs, never a newly observed tip:
1. Record `kstack-git scratch-digest` at creation; `kstack-git delete-scratch --expect DIGEST` uses that inventory digest on every return.
2. `kstack-git delete-remote-branch`.
3. `kstack-git remove-worktree` for disposable worktrees.
4. `kstack-git delete-local-branch` with recorded config digest; absent ref + config: retained.
5. `kstack-git sync-local` last.

Only done/absent = cleaned. Report delivery/cleanup/sync separately; retained/error is partial.
