---
name: kstack-no-comments
description: Delete unjustified comments and fix the workarounds they excuse.
disable-model-invocation: true
---

# kstack-no-comments

Shared rules: read `../kstack/SKILL.md` first; `../kstack/references/dispatch.md` before starting the agent.

Scope: caller's files/diff; otherwise the diff against base (default `main`) including the working tree.

1. **Hunt.** Fresh configured reviewer, read-only, never the author. Brief: scope plus the lists below. Every other comment is a kill; doubt is a kill. Return `file:line | KILL/KEEP/MUST KILL | symbol | reason`.
   - Keep: legal/license headers; public API doc comments defining a contract; issue/RFC links for constraints code cannot express; formatter ignores; lint suppressions of faulty/pedantic/style-only rules; non-obvious behavior forced by an external dependency/platform/vendor/protocol we cannot reshape, proven true today on a live path.
   - `MUST KILL`, naming the exact symbol to rename/extract/type/restructure: surprises in our own code; suppressions of correctness/safety rules; `IMPORTANT`/`do not remove`/`fine for now`/long justifications without a proven keep.
2. **Judge.** Check the report against code. Reject out-of-scope flags, kills of keep-list comments and `MUST KILL` reasons the code refutes. Thin keeps/kills: trace the symbol's callers and history first. Ambiguous kills stay killed; refuted/ambiguous keeps die. Rejected report: rerun once naming the failure; second rejection is BLOCKED.
3. **Delete** accepted kills: comments only, never reworded into shorter excuses.
4. **Fix** each `MUST KILL` at root cause in scope: delete the dead path, drop the parameter, use the real API, rename. Remove every named workaround; no symptom guards. Needs design or leaves scope: land the smallest in-scope fix, report the rest for kstack-plan.
5. **Constraints** on our own code (`do not remove`, `do not change wording`, `talk to X before changing`): offer the cheapest in-scope type/runtime check/test/lint and wait for approval; unattended runs need caller pre-approval. Approved: encode, then delete. Otherwise delete and report the constraint unenforced as a kstack-improve candidate.
6. Run project checks.

Report deletion count, keeps with proof, reruns, fixes, encoding offers/encodings, unenforced constraints and open work.
