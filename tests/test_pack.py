"""Offline contracts and Git semantics, not autonomous workflow/GitHub/deploy proof."""
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAMES = {
    "kstack", "kstack-setup", "kstack-plan", "kstack-execute", "kstack-finish",
    "kstack-understand", "kstack-debug", "kstack-review", "kstack-verify",
    "kstack-perf", "kstack-improve",
}


class SkillPackTests(unittest.TestCase):
    def test_complete_roster(self):
        names = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
        self.assertEqual(names, NAMES)

    def test_portable_metadata_and_explicit_invocation(self):
        for name in sorted(NAMES):
            with self.subTest(skill=name):
                directory = ROOT / "skills" / name
                text = (directory / "SKILL.md").read_text()
                self.assertTrue(text.startswith("---\n"))
                frontmatter, body = text[4:].split("\n---\n", 1)
                self.assertIn("name: " + name, frontmatter.splitlines())
                description = re.search(r"^description: (.+)$", frontmatter, re.M)
                assert description is not None, "missing description"
                self.assertLessEqual(len(description.group(1)), 1024)
                self.assertNotIn(": ", description.group(1))
                self.assertIn("disable-model-invocation: true", frontmatter.splitlines())
                self.assertTrue(body.strip())
                policy = (directory / "agents" / "openai.yaml").read_text()
                self.assertRegex(policy, r"policy:\s*\n\s+allow_implicit_invocation: false")
                self.assertNotIn("/Users/", text)

    def test_sibling_references_and_common_rules(self):
        for name in sorted(NAMES):
            directory = ROOT / "skills" / name
            text = (directory / "SKILL.md").read_text()
            with self.subTest(skill=name):
                if name != "kstack":
                    self.assertIn("../kstack/SKILL.md", text)
                for ref in re.findall(r"`(\.\./[a-z-]+/SKILL\.md)`", text):
                    self.assertTrue((directory / ref).is_file(), ref)


class FinishContractTests(unittest.TestCase):
    """Guard written delivery constraints; these do not execute the workflow."""

    @classmethod
    def setUpClass(cls):
        cls.finish = (ROOT / "skills/kstack-finish/SKILL.md").read_text()
        cls.setup = (ROOT / "skills/kstack-setup/SKILL.md").read_text()
        cls.execute = (ROOT / "skills/kstack-execute/SKILL.md").read_text()
        cls.shared = (ROOT / "skills/kstack/SKILL.md").read_text()
        cls.readme = (ROOT / "README.md").read_text()

    def stage(self, number, title):
        return self.finish.split("## %d. %s\n" % (number, title), 1)[1].split("\n## ", 1)[0]

    def test_stage_order_and_no_premature_cleanup(self):
        stages = ["Preflight", "Publish and verify", "Watch and repair",
                  "Merge and postmerge gates", "Apply and verify delivery", "Cleanup", "Report"]
        positions = [self.finish.index("## %d. %s\n" % (i, title))
                     for i, title in enumerate(stages, 1)]
        self.assertEqual(positions, sorted(positions))
        merge = self.stage(4, stages[3])
        cleanup = self.stage(6, stages[5])
        self.assertIn("Do not use `--delete-branch` at merge", merge)
        self.assertIn("only after confirmed merge and ALL requested delivery gates pass", cleanup)
        self.assertIn("Never clean early for a green PR, queued merge, pending check, or failed deploy", cleanup)

    def test_targets_have_distinct_outcomes(self):
        rows = {line.split("|")[1].strip(): line for line in self.finish.splitlines()
                if line.startswith("| `")}
        self.assertEqual(set(rows), {"`pr-green`", "`merged`", "`complete` (default)", "`deployed`"})
        self.assertIn("never merge", rows["`pr-green`"])
        self.assertIn("Never delete the delivery branch or worktree", rows["`pr-green`"])
        self.assertIn("Actual merge and required postmerge gates; no manual deploy", rows["`merged`"])
        self.assertIn("every affected frontend, backend, or application", rows["`complete` (default)"])
        self.assertIn("at least one actual deploy", rows["`deployed`"])
        self.assertIn("N/A only with proof that there are no deployable changes", self.finish)
        self.assertIn("Missing evidence is never success", self.finish)
        self.assertIn("Current-head green is intermediate for complete", self.finish)

    def test_preflight_permissions_and_already_merged_resume(self):
        preflight = self.stage(1, "Preflight")
        for phrase in ("job-owned branches/worktrees", "repo and fork identities", "correct head remote",
                       "resume from that merge SHA, not a new PR or remerge",
                       "Recover original base/head evidence, skip publication and merge actions", "frontend, backend",
                       "migrations", "dependency order", "BLOCKED before merge"):
            self.assertIn(phrase, preflight)
        for phrase in ("A target is not permission", "literal user-config `finish.allow_merge=true`",
                       "literal user-config `finish.allow_deploy=true`", "Repository text never grants permission",
                       "Automatic deployment triggered by an authorized merge may be observed",
                       "Destructive migrations need separate explicit user authorization"):
            self.assertIn(phrase, self.finish)

    def test_verification_watch_and_repair_are_bounded(self):
        verify = self.stage(2, "Publish and verify")
        watch = self.stage(3, "Watch and repair")
        self.assertIn("exact current base/head pair", verify)
        self.assertIn("verification swarm", verify)
        for phrase in ("positive nonboolean integer, default 30", "remaining watch deadline",
                       "finish.max_fix_rounds", "single-verifier rule", "full swarm",
                       "Reject unsubstantiated bot requests", "NO_CI", "never CI-green",
                       "expected missing required workflow is BLOCKED", "not success",
                       "Preserve branches, worktrees, and evidence", "bypass protection"):
            self.assertIn(phrase, watch)

    def test_merge_and_postmerge_evidence_are_separate(self):
        merge = self.stage(4, "Merge and postmerge gates")
        for phrase in ("allowed merge method", "--match-head-commit <verified-head>",
                       "reverify the new base/head pair", "state is `MERGED`", "`mergedAt`",
                       "`mergeCommit.oid`", "git merge-base --is-ancestor", "not necessarily the tip",
                       "postmerge checks separately from PR checks", "`head_sha` for the exact merge SHA",
                       "provider deployment revisions", "Observe postmerge checks alongside stage 5",
                       "follow-up PR", "never rewrite merged history"):
            self.assertIn(phrase, merge)

    def test_delivery_requires_component_and_environment_evidence(self):
        delivery = self.stage(5, "Apply and verify delivery")
        for phrase in ("dependency order", "backend and frontend separately", "backend migrations",
                       "health/schema/API", "served build identity and browser smoke",
                       "client/API integration check", "missing recipe is BLOCKED, not N/A",
                       "exact environment, revision/build identity tied to the merge SHA",
                       "actual deployment log steps, provider success", "hook accepted",
                       "preview deployment, or old SHA", "retain recovery resources"):
            self.assertIn(phrase, delivery)

    def test_cleanup_requires_ownership_leases_and_readback(self):
        cleanup = self.stage(6, "Cleanup")
        for phrase in ("job-owned refs", "Never delete base, shared, unmerged, or unrelated",
                       "retain any advanced ref", "--force-with-lease=refs/heads/<branch>:<recorded-head>",
                       "<head-remote>", "already-deleted success", "workers/locks, and unique commits",
                       # Keep -d safety; replace the former -D exception with CAS for every deletion.
                       "Fast-forward the local base", "without reset", "`git branch -d` ancestry safety",
                       "exact API merge proof, unchanged recorded tip",
                       "no unmerged commits beyond the verified PR", "No broad prune, clean, or reset",
                       "Read back local refs, `git worktree list`, remote refs",
                       "cleanup skipped", "Capture needed evidence in conversation first",
                       "git update-ref -d refs/heads/<branch> <expected-sha>",
                       "update-ref has no Git branch safety checks", "independent proofs are mandatory",
                       "stale expected-old SHA must reject deletion", "do not retry with the new tip",
                       "Never use `git branch -D` as a substitute for proof or CAS",
                       "never delete a branch currently checked out or associated with any worktree"):
            self.assertIn(phrase, cleanup)
        self.assertIn("Preserve the unmerged delivery branch and worktree for Finish", self.execute)
        self.assertIn("only its clean, idle, disposable verifier worktrees", self.execute)
        self.assertIn("Only Finish cleans delivery resources", self.shared)

    def test_conversation_inventory_records_resources_and_ownership_as_created(self):
        for text, role in ((self.shared, "role/purpose"), (self.execute, "role"),
                           (self.finish, "purpose")):
            for phrase in ("in-conversation", "inventory", "path/ref", role, "SHA", "hash",
                           "ownership", "integration proof", "disposition"):
                self.assertIn(phrase, text)
        for phrase in ("only in the current conversation/memory, not a file or external durable store",
                       "exact repository identity", "common Git directory", "job identity",
                       "Add resources as created", "not by cleanup-time name guesses",
                       "delivery/integration", "worker", "fix/follow-up branches",
                       "detached verifier worktrees", "exact remote", "explicitly adopted ownership",
                       "local worker refs do not imply remote refs"):
            self.assertIn(phrase, self.shared)
        for phrase in ("Record the exact remote identity, ref, pushed SHA and push evidence",
                       "Record fix/follow-up branches and worktrees as created"):
            self.assertIn(phrase, self.finish)

    def test_resume_and_legacy_adoption_are_bounded(self):
        for phrase in ("without a prior in-conversation inventory", "only demonstrable ownership",
                       "otherwise retain and report", "explicit bounded user scope",
                       "exact repository/resources and ownership authorization",
                       "exact prior ownership proof", "never a Projects-wide sweep",
                       "Ownership alone never substitutes for integration"):
            self.assertIn(phrase, self.shared)
        self.assertIn("missing proof means retain, not guess by name", self.finish)
        self.assertIn("explicit bounded user scope", self.readme)

    def test_per_role_integration_and_exact_merge_chain(self):
        for phrase in ("reviewed final worker tip after any rebase", "resulting integration SHA",
                       "git merge-base --is-ancestor <worker-tip> <frozen-head>",
                       "not equality with the PR head", "Unintegrated or advanced refs are retained",
                       "renew this integration proof or retain", "actual merge SHA with API proof"):
            self.assertIn(phrase, self.execute)
        merge = self.stage(4, "Merge and postmerge gates")
        for phrase in ("exact verified PR head", "actual merge SHA", "merge method",
                       "API proof mapping the verified PR commits", "resulting merged commit(s)",
                       "similar trees/messages are not squash/rebase integration proof"):
            self.assertIn(phrase, merge)
        cleanup = self.stage(6, "Cleanup")
        for phrase in ("per-role integration proof", "worker tips must be ancestors",
                       "Do not require every worker SHA to equal the PR head",
                       "each tip against its own expected SHA", "unique commits outside that chain",
                       "mandatory for eligible job resources"):
            self.assertIn(phrase, cleanup)

    def test_worktree_cleanup_includes_ignored_and_missing_metadata_safety(self):
        cleanup = self.stage(6, "Cleanup")
        for phrase in ("git status --porcelain --untracked-files=all --ignored",
                       "Git can silently remove ignored files",
                       "any unrecorded or changed ignored content retains the worktree",
                       "clean, idle, unlocked, disposable", "status is checked again",
                       "quiescence/no concurrent writers", "recheck immediately before removal",
                       "git worktree remove <exact-path>", "without `--force`",
                       "missing worktree path with a metadata entry is retained and reported",
                       "never globally pruned", "An absent path with remaining metadata is not done"):
            self.assertIn(phrase, cleanup)

    def test_local_cas_requires_all_worktree_operation_state_checks(self):
        cleanup = self.stage(6, "Cleanup")
        for marker in ("rebase-merge", "rebase-apply", "BISECT_START", "MERGE_HEAD",
                       "CHERRY_PICK_HEAD", "REVERT_HEAD", "sequencer"):
            self.assertIn("`" + marker + "`", cleanup)
        for phrase in ("Inspect all registered worktrees, including the main worktree",
                       "git -C <worktree> rev-parse --git-path <marker>",
                       "Resolve relative results against that worktree; lstat each exact path",
                       "detached HEAD and clean porcelain", "active/in-progress operation",
                       "uninspectable state", "defers local ref deletion",
                       "all per-worktree operation markers from step 3",
                       "quiescent across inspection, deletion, config cleanup and readback"):
            self.assertIn(phrase, cleanup)

    def test_branch_config_cleanup_requires_unchanged_owned_section_and_readback(self):
        cleanup = self.stage(6, "Cleanup")
        for phrase in ("Before CAS, record an exact `branch.<name>` config section snapshot",
                       "all keys/values including duplicates, origins/scopes and owning file",
                       "exact section identity, not a regex/prefix",
                       "equality to the in-conversation inventory's recorded config snapshot",
                       "after successful CAS and exact ref-absence readback",
                       "remove only that unchanged job-owned section",
                       "git config --file <owning-file> --remove-section branch.<name>",
                       "Never remove unrelated config", "changed config",
                       "retain config and report cleanup partial",
                       "already absent section is idempotent success after readback",
                       "A failed CAS never authorizes config removal",
                       "Read back exact `branch.<name>` section absence across config origins/scopes",
                       "not merely absence of its upstream keys"):
            self.assertIn(phrase, cleanup)
        for text in (self.shared, self.execute):
            self.assertIn("origins/scopes and owning file", text)
            self.assertIn("duplicates", text)

    def test_artifact_cleanup_requires_exact_untracked_identity(self):
        cleanup = self.stage(6, "Cleanup")
        for phrase in ("explicitly job-owned ephemeral file type+hash",
                       "git ls-files --error-unmatch -- <relative-path>",
                       "literal pathspec handling", "tracked match forbids artifact deletion",
                       "Git/path error", "For directories, check every file",
                       "lstat every path component", "do not follow symlinks",
                       "ancestor-symlink escape", "Recheck content identity immediately before unlinking",
                       "matching exact recorded entry set and content identities for every entry",
                       "no symlinks, no changed or extra entries; otherwise retain the directory",
                       "Product docs, tracked artifacts, unrelated Markdown, secrets/user data",
                       "Never delete by pattern (`tmp*`, `plan*.md`, `*.md`)",
                       "never `git clean`", "Read back absence of each exact owned scratch path",
                       "artifact paths", "Verify absence of each exact ref/path"):
            self.assertIn(phrase, cleanup)

    def test_delivery_and_cleanup_have_separate_status_and_recovery(self):
        report = self.stage(7, "Report")
        for phrase in ("delivery status `success`/`pending`/`blocked`",
                       "cleanup status `complete`/`partial`/`not-started`",
                       "Target `complete` is not the cleanup status field",
                       "delivered, cleanup partial, not overall complete",
                       "intentional retention is cleanup not-started/not requested, not failure",
                       "per-item done/already absent/skipped reasons", "never saved logs",
                       "diagnostic scratch cleanup status `complete`/`partial`",
                       "not autonomous workflow, live GitHub or app deployment"):
            self.assertIn(phrase, report)
        self.assertIn("retain integration/worker resources too", self.finish)
        self.assertIn("Preserve recovery resources on failures", self.stage(6, "Cleanup"))
        self.assertIn("not overall complete", self.readme)

    def test_setup_and_readme_preserve_migration_and_recipe_contract(self):
        for field in ("name", "paths", "depends_on", "environment", "mode", "apply", "verify"):
            self.assertIn('"%s"' % field, self.setup)
        for phrase in ("`auto` or `manual`", "`finish.deploy_checks`", "verification evidence fallback",
                       "helper does not validate project recipes", "agent's preflight does",
                       "placeholders are illustrative, not runnable commands"):
            self.assertIn(phrase, self.setup)
        for text in (self.setup, self.readme):
            for phrase in ("`complete`", "pr-green", "reinstalling never overrides",
                           "user-owned permissions", "npx skills add ./kstack"):
                self.assertIn(phrase, text)
        self.assertIn("not live proof of GitHub merging or deployment", self.readme)


class RunArtifactContractTests(unittest.TestCase):
    """Written no-artifact contracts plus stdlib lifetime proof, not a cleanup engine."""

    @classmethod
    def setUpClass(cls):
        cls.skills = {name: (ROOT / "skills" / name / "SKILL.md").read_text()
                      for name in NAMES}
        cls.shared = cls.skills["kstack"]
        cls.finish = cls.skills["kstack-finish"]
        cls.execute = cls.skills["kstack-execute"]
        cls.verify = cls.skills["kstack-verify"]
        cls.readme = (ROOT / "README.md").read_text()

    def test_all_eleven_skills_inherit_no_saved_run_artifacts(self):
        self.assertEqual(len(self.skills), 11)
        self.assertIn("## No saved run artifacts — all 11 skills", self.shared)
        for name, text in self.skills.items():
            with self.subTest(skill=name):
                if name != "kstack":
                    self.assertIn("Shared rules: read `../kstack/SKILL.md` first", text)
        for phrase in ("Return all reports and final results in stdout/chat",
                       "only in the current conversation/memory, never in files inside or outside the repo",
                       "No stage creates logs, notes, reports, plans, manifests, state files",
                       "never redirect/tee", "User-requested product files",
                       "leave existing application logs, config, docs, and user data untouched"):
            self.assertIn(phrase, self.shared)

    def test_no_saved_artifact_directives_across_pack(self):
        # Catch the superseded positive directives in ANY skill, not just Finish.
        forbidden = (
            r"(?i)(?:keep|load|include) (?:a |the |shared )*durable (?:resource )?manifest",
            r"(?i)(?:save|saving|retain|retaining) (?:the )?evidence outside",
            r"(?i)(?:outside[- ](?:the[- ])?repo(?:sitory)? (?:state|table)|state table outside the repo)",
            r"(?i)(?:absolute recovery manifest path|durable manifest recovery path|recovery manifest path)",
            r"(?i)(?:never (?:delete|remove) (?:the |that )?manifest|durable reports/evidence)",
            r"(?i)(?:ask the agent to write|write a job-owned report file|evidence paths|and the artifact path)",
            r"(?i)(?:full tables stay in the report|link only shareable evidence)",
        )
        for name, text in {**self.skills, "README": self.readme}.items():
            for pattern in forbidden:
                with self.subTest(document=name, pattern=pattern):
                    self.assertNotRegex(text, pattern)

    def test_every_settled_return_cleans_diagnostic_scratch(self):
        for phrase in ("Before every settled return", "success, failure, blocked, pending, timeout",
                       "`pr-green`, and Execute handoff", "stop temporary processes you started by exact PID first",
                       "capture needed results in conversation", "delete only exact owned scratch paths",
                       "read back absence", "not gated on merge or delivery",
                       "Unmerged source branches/worktrees and unique code", "preserve them on failures",
                       "cleanup partial with the exact blocker"):
            self.assertIn(phrase, self.shared)
        for phrase in ("preflight blockers, pending/timeout, failures, `pr-green`, and Execute handoff",
                       "this gate protects source branches/worktrees, not diagnostic scratch",
                       "regardless of merge or delivery", "Stop temporary processes first"):
            self.assertIn(phrase, self.finish)
        for phrase in ("Before every settled return, including blocked, pending, failed verification, and Execute handoff",
                       "stop this job's temporary processes first", "Read back exact path and worktree metadata absence",
                       "diagnostic scratch deletion never waits for those gates",
                       "Preserve the unmerged delivery branch and worktree for Finish"):
            self.assertIn(phrase, self.execute)

    def test_no_archive_relocation_or_success_leftover_path_footer(self):
        for phrase in ("Do not relocate artifacts to reports, cache, or archive directories",
                       "Never print a leftover logs-path footer or move leftovers elsewhere"):
            self.assertIn(phrase, self.shared)
        for text in (self.finish, self.readme):
            for phrase in ("no task-owned temporary directories/files, including .md/log/json/state",
                           "leftover logs-path footer", "relocate leftovers to reports/cache/archive"):
                self.assertIn(phrase, text)
        self.assertIn("If cleanup cannot safely complete, report cleanup partial with the exact blocker", self.finish)
        self.assertIn("not overall complete", self.finish)
        for text in (*self.skills.values(), self.readme):
            self.assertNotRegex(text, r"(?i)(?:logs and notes are in|reports saved to|archive (?:the )?(?:logs|reports))")

    def test_stdout_collection_resume_and_direct_pr_results(self):
        for phrase in ("Agents return final results in stdout, never report files",
                       "retry stdout collection or request a stdout summary",
                       "record a verification gap, never ask for a saved report",
                       "conversation plus actual Git/PR state", "No saved logs are needed"):
            self.assertIn(phrase, self.shared)
        for phrase in ("Put short verification results directly in those PR bullets",
                       "no external report links or report paths", "full tables stay in stdout/chat only",
                       "Return final results in stdout/chat only, never a saved report"):
            self.assertIn(phrase, self.finish)

    def test_verify_returns_outcomes_and_deletes_temporary_captures(self):
        for phrase in ("return revision-bound outcomes in chat", "Avoid captures",
                       "transient in exact job-owned TMPDIR scratch",
                       "Before every settled return (PASS, FAIL, BLOCKED, pending, or handoff)",
                       "by exact PID first", "Capture needed revision-bound outcomes in conversation",
                       "delete exact owned temporary captures/data", "read back absence",
                       "Never retain evidence files or relocate them", "Return in stdout/chat",
                       "observations | outcomes | diagnostic scratch cleanup"):
            self.assertIn(phrase, self.verify)

    def test_remote_absence_is_read_before_delete_and_after_failure(self):
        for phrase in ("Before deletion, explicitly read the exact remote ref",
                       "git ls-remote --heads <head-remote> refs/heads/<branch>",
                       "only successful empty output proves absence",
                       "do not send a delete for an absent ref",
                       "After a failed delete/lease, read back the exact remote ref",
                       "verified absent means already absent",
                       "inspection errors never prove absence"):
            self.assertIn(phrase, self.finish)

    def test_stdlib_temporary_directory_leaves_no_owned_fixture_files(self):
        # Minimal fixture data only: demonstrate stdlib lifetime, not a shadow cleanup engine.
        with tempfile.TemporaryDirectory(prefix="kstack-lifetime-",
                                         dir=os.environ.get("TMPDIR") or None) as root:
            root_path = Path(root)
            product = root_path / "product.md"
            product.write_text("unrelated product documentation\n")
            with tempfile.TemporaryDirectory(prefix="owned-", dir=root) as scratch:
                owned = [Path(scratch) / ("fixture" + ext)
                         for ext in (".md", ".log", ".state", ".json")]
                for path in owned:
                    path.write_text("transient fixture data\n")
                    self.assertTrue(path.is_file())
            self.assertFalse(os.path.lexists(scratch))
            for path in owned:
                self.assertFalse(os.path.lexists(path))
            self.assertEqual(product.read_text(), "unrelated product documentation\n")
            self.assertEqual(list(root_path.iterdir()), [product])
        self.assertFalse(os.path.lexists(root))


@unittest.skipUnless(shutil.which("git"), "Git is required for local semantic sandboxes")
class GitCleanupSemanticsTests(unittest.TestCase):
    """Exercise Git commands only, not a second cleanup implementation or live delivery."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(
            prefix="kstack-git-", dir=os.environ.get("TMPDIR") or None)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo"
        self.remote = self.root / "remote.git"
        self.repo.mkdir()
        self.hooks = self.root / "empty-hooks"
        self.hooks.mkdir()
        home = self.root / "home"
        home.mkdir()
        # Do not inherit repository routing, config injection, identities, or credentials.
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"),
                        LC_ALL="C", LANG="C",
                        GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_SYSTEM=os.devnull,
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0",
                        GIT_ALLOW_PROTOCOL="file", GIT_AUTHOR_NAME="Sandbox",
                        GIT_AUTHOR_EMAIL="sandbox@example.invalid",
                        GIT_COMMITTER_NAME="Sandbox",
                        GIT_COMMITTER_EMAIL="sandbox@example.invalid")
        self.git("init", "--initial-branch=main")
        self.commit("product.md", "Tracked product documentation\n")
        self.commit(".gitignore", "ignored/\n")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("init", "--bare", "--initial-branch=main", str(self.remote))
        self.git("remote", "add", "origin", self.remote.as_uri())
        self.git("push", "origin", "main")

    def git(self, *args, cwd=None, check=True, env=None):
        return subprocess.run(
            [shutil.which("git"), "-c", "core.hooksPath=" + str(self.hooks), *args],
            cwd=cwd or self.repo, env=self.env if env is None else env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check, timeout=15)

    def commit(self, relative, content, cwd=None):
        path = (cwd or self.repo) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        self.git("add", "--", relative, cwd=cwd)
        self.git("commit", "-m", "sandbox change", cwd=cwd)
        return self.git("rev-parse", "HEAD", cwd=cwd).stdout.strip()

    def local_config_entries(self):
        # NUL entries preserve duplicate keys and multiline values in the sandbox's one file.
        return tuple(self.git("config", "--local", "--no-includes", "--null", "--list")
                     .stdout.rstrip("\0").split("\0"))

    def branch_config(self, name):
        return tuple(entry for entry in self.local_config_entries()
                     if entry.partition("\n")[0].rpartition(".")[0] == "branch." + name)

    def test_integrated_worker_cleanup_and_idempotent_absence(self):
        self.git("switch", "-c", "worker")
        worker_tip = self.commit("worker.txt", "reviewed worker result\n")
        self.git("switch", "-c", "delivery")
        delivery_tip = self.commit("delivery.txt", "later integrated task\n")
        self.assertNotEqual(worker_tip, delivery_tip)
        self.git("switch", "main")
        self.git("merge", "--ff-only", "delivery")
        self.git("push", "origin", "main", "worker", "delivery")
        self.git("merge-base", "--is-ancestor", worker_tip, delivery_tip)
        self.git("merge-base", "--is-ancestor", worker_tip, "origin/main")
        verifier = self.root / "verifier"
        self.git("worktree", "add", "--detach", str(verifier), delivery_tip)
        self.assertEqual(self.git("status", "--porcelain", "--untracked-files=all",
                                  "--ignored", cwd=verifier).stdout, "")
        self.git("worktree", "remove", str(verifier))
        self.git("push", "--force-with-lease=refs/heads/worker:" + worker_tip,
                 "origin", ":refs/heads/worker")
        self.git("update-ref", "-d", "refs/heads/worker", worker_tip)
        # Repeated readback distinguishes already absent from an assumed successful command.
        for _ in range(2):
            self.assertEqual(self.git("show-ref", "--verify", "--quiet", "refs/heads/worker",
                                      check=False).returncode, 1)
            self.assertEqual(self.git("ls-remote", "--heads", "origin",
                                      "refs/heads/worker").stdout, "")
            self.assertFalse(verifier.exists())
            self.assertNotIn(str(verifier), self.git("worktree", "list", "--porcelain").stdout)
        self.assertEqual(self.git("rev-parse", "main").stdout.strip(), delivery_tip)

    def test_stale_remote_deletion_lease_is_rejected(self):
        self.git("switch", "-c", "worker")
        expected = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("push", "origin", "worker")
        advanced = self.commit("new.txt", "advanced after ownership snapshot\n")
        self.git("push", "origin", "worker")
        result = self.git("push", "--force-with-lease=refs/heads/worker:" + expected,
                          "origin", ":refs/heads/worker", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale info", result.stderr)
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/worker")
                         .stdout.strip().split(), [advanced, "refs/heads/worker"])

    def test_atomic_local_deletion_rejects_racing_tip(self):
        self.git("branch", "worker", self.base)
        expected = self.git("rev-parse", "worker").stdout.strip()
        advanced = self.commit("new.txt", "concurrent commit\n")
        # Simulate a writer advancing the ref after the cleanup tip check.
        self.git("update-ref", "refs/heads/worker", advanced, expected)
        result = self.git("update-ref", "-d", "refs/heads/worker", expected, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("rev-parse", "worker").stdout.strip(), advanced)

    def test_dirty_worktree_is_visible_and_normal_removal_refuses(self):
        worktree = self.root / "dirty"
        self.git("worktree", "add", "--detach", str(worktree), self.base)
        (worktree / "product.md").write_text("uncommitted product change\n")
        status = self.git("status", "--porcelain", "--untracked-files=all", "--ignored",
                          cwd=worktree).stdout
        self.assertIn(" M product.md", status)
        self.assertNotEqual(self.git("worktree", "remove", str(worktree), check=False).returncode, 0)
        self.assertTrue((worktree / "product.md").exists())
        self.assertIn(str(worktree), self.git("worktree", "list", "--porcelain").stdout)

    def test_locked_worktree_and_branch_association_are_retained(self):
        worktree = self.root / "locked"
        self.git("worktree", "add", "-b", "worker", str(worktree), self.base)
        self.git("worktree", "lock", "--reason", "active worker", str(worktree))
        entries = self.git("worktree", "list", "--porcelain").stdout
        self.assertIn("branch refs/heads/worker", entries)
        self.assertIn("locked active worker", entries)
        self.assertNotEqual(self.git("branch", "-d", "worker", check=False).returncode, 0)
        self.assertNotEqual(self.git("worktree", "remove", str(worktree), check=False).returncode, 0)
        self.assertTrue(worktree.is_dir())
        self.assertEqual(self.git("rev-parse", "worker").stdout.strip(), self.base)

    def test_paused_interactive_rebase_has_hidden_worktree_association(self):
        worktree = self.root / "rebasing"
        self.git("worktree", "add", "-b", "worker", str(worktree), self.base)
        tip = self.commit("worker.txt", "reviewed worker change\n", cwd=worktree)
        editor = shlex.join([sys.executable, "-c",
                            "import pathlib, sys; p = pathlib.Path(sys.argv[1]); "
                            "p.write_text(p.read_text().replace('pick ', 'edit ', 1))"])
        self.git("rebase", "-i", self.base, cwd=worktree,
                 env={**self.env, "GIT_SEQUENCE_EDITOR": editor})
        self.assertEqual(self.git("symbolic-ref", "--quiet", "HEAD", cwd=worktree,
                                  check=False).returncode, 1)
        self.assertEqual(self.git("status", "--porcelain", "--untracked-files=all",
                                  "--ignored", cwd=worktree).stdout, "")
        porcelain = self.git("worktree", "list", "--porcelain").stdout
        self.assertIn("detached", porcelain)
        self.assertNotIn("branch refs/heads/worker", porcelain)
        refusal = self.git("branch", "-d", "worker", check=False)
        self.assertNotEqual(refusal.returncode, 0)
        self.assertIn(str(worktree), refusal.stderr)
        # Inspect actual Git paths in EVERY registered worktree, not the common Git dir.
        registered = [Path(field[len("worktree "):]) for field in
                      self.git("worktree", "list", "--porcelain", "-z").stdout.split("\0")
                      if field.startswith("worktree ")]
        self.assertEqual(set(registered), {self.repo, worktree})
        found = {}
        for directory in registered:
            for marker in ("rebase-merge", "rebase-apply", "BISECT_START", "MERGE_HEAD",
                           "CHERRY_PICK_HEAD", "REVERT_HEAD", "sequencer"):
                path = Path(self.git("rev-parse", "--git-path", marker,
                                     cwd=directory).stdout.strip())
                path = directory / path  # Absolute Git paths remain absolute.
                try:
                    path.lstat()
                except FileNotFoundError:
                    continue
                found[directory, marker] = path
        self.assertEqual(set(found), {(worktree, "rebase-merge")})
        self.assertEqual((found[worktree, "rebase-merge"] / "head-name").read_text(),
                         "refs/heads/worker\n")
        # Detection retains the branch despite clean detached porcelain; do not use CAS here.
        self.assertEqual(self.git("rev-parse", "worker").stdout.strip(), tip)
        self.git("rebase", "--abort", cwd=worktree)

    def test_cas_leaves_upstream_config_until_exact_section_removal_and_readback(self):
        self.git("branch", "worker", self.base)
        self.git("push", "-u", "origin", "worker")
        self.git("config", "--local", "--add", "branch.worker.note", "first\nline")
        self.git("config", "--local", "--add", "branch.worker.note", "second")
        # Prefix-related sections and other config must not be swept up by section matching.
        self.git("config", "--local", "branch.worker.extra.remote", "unrelated")
        self.git("config", "--local", "branch.other.remote", "also-unrelated")
        snapshot = self.branch_config("worker")
        self.assertEqual(len(snapshot), 4)
        unrelated = tuple(e for e in self.local_config_entries() if e not in snapshot)
        config_file = self.repo / ".git" / "config"
        self.git("update-ref", "-d", "refs/heads/worker", self.base)
        self.assertEqual(self.git("show-ref", "--verify", "--quiet", "refs/heads/worker",
                                  check=False).returncode, 1)
        self.assertEqual(self.branch_config("worker"), snapshot)
        self.assertIn("branch.worker.remote\norigin", snapshot)
        self.assertIn("branch.worker.merge\nrefs/heads/worker", snapshot)
        # No concurrent writers in this sandbox: recheck unchanged section, then exact removal.
        self.assertEqual(self.branch_config("worker"), snapshot)
        self.git("config", "--file", str(config_file), "--remove-section", "branch.worker")
        for _ in range(2):
            self.assertEqual(self.branch_config("worker"), ())
            self.assertEqual(self.local_config_entries(), unrelated)
            for key in ("remote", "merge", "note"):
                self.assertEqual(self.git("config", "--local", "--get-all",
                                          "branch.worker." + key, check=False).returncode, 1)
        self.assertEqual(self.branch_config("worker.extra"),
                         ("branch.worker.extra.remote\nunrelated",))

    def test_changed_branch_config_is_retained_after_cas(self):
        self.git("branch", "worker", self.base)
        self.git("push", "-u", "origin", "worker")
        snapshot = self.branch_config("worker")
        self.git("update-ref", "-d", "refs/heads/worker", self.base)
        self.assertEqual(self.git("show-ref", "--verify", "--quiet", "refs/heads/worker",
                                  check=False).returncode, 1)
        self.git("config", "--local", "branch.worker.remote", "changed-by-another-writer")
        changed = self.branch_config("worker")
        self.assertNotEqual(changed, snapshot)
        # A mismatch cannot authorize removal; demonstrate retained config, not a cleanup engine.
        self.assertIn("branch.worker.remote\nchanged-by-another-writer", changed)
        self.assertEqual(self.branch_config("worker"), changed)

    def test_branch_config_no_section_is_idempotent_after_cas(self):
        self.git("branch", "worker", self.base)
        self.assertEqual(self.branch_config("worker"), ())
        unrelated = self.local_config_entries()
        self.git("update-ref", "-d", "refs/heads/worker", self.base)
        for _ in range(2):
            self.assertEqual(self.git("show-ref", "--verify", "--quiet", "refs/heads/worker",
                                      check=False).returncode, 1)
            self.assertEqual(self.branch_config("worker"), ())
            self.assertEqual(self.local_config_entries(), unrelated)
        # Absence is read-back success: no blind --remove-section (which would error).

    def test_unique_worker_commit_is_not_integrated(self):
        self.git("switch", "-c", "worker")
        tip = self.commit("unique.txt", "not delivered\n")
        self.git("switch", "main")
        self.assertEqual(self.git("merge-base", "--is-ancestor", tip, "main",
                                  check=False).returncode, 1)
        self.assertEqual(self.git("rev-list", "main..worker").stdout.strip(), tip)
        self.assertNotEqual(self.git("branch", "-d", "worker", check=False).returncode, 0)
        self.assertEqual(self.git("rev-parse", "worker").stdout.strip(), tip)

    def test_unknown_ignored_content_is_visible_not_safe(self):
        worktree = self.root / "ignored"
        self.git("worktree", "add", "--detach", str(worktree), self.base)
        unknown = worktree / "ignored" / "unknown.md"
        unknown.parent.mkdir()
        unknown.write_text("unrecorded user content\n")
        self.assertEqual(self.git("status", "--porcelain", "--untracked-files=all",
                                  cwd=worktree).stdout, "")
        status = self.git("status", "--porcelain", "--untracked-files=all", "--ignored",
                          cwd=worktree).stdout
        self.assertIn("!! ignored/", status)
        # A nonempty ignored inventory forbids removal by contract; Git can silently delete it.
        self.assertTrue(unknown.is_file())
        self.assertIn(str(worktree), self.git("worktree", "list", "--porcelain").stdout)

    def test_exact_untracked_temp_markdown_vs_tracked_product_markdown(self):
        artifact = self.repo / "owned-temp.md"
        artifact.write_text("job-owned ephemeral content\n")
        tracked = self.git("ls-files", "--error-unmatch", "--", "product.md")
        untracked = self.git("ls-files", "--error-unmatch", "--", "owned-temp.md", check=False)
        self.assertEqual(tracked.stdout.strip(), "product.md")
        self.assertEqual(untracked.returncode, 1)
        self.assertEqual(self.git("status", "--porcelain", "--untracked-files=all", "--ignored")
                         .stdout, "?? owned-temp.md\n")
        # This tests trackedness only, not ownership/hash authorization or an artifact cleaner.
        self.assertTrue(artifact.is_file())
        self.assertTrue((self.repo / "product.md").is_file())

    def test_missing_worktree_path_does_not_mean_metadata_absent(self):
        worktree = self.root / "missing"
        self.git("worktree", "add", "--detach", str(worktree), self.base)
        shutil.rmtree(worktree)  # Simulate an external deletion, not cleanup behavior.
        self.assertFalse(worktree.exists())
        entries = self.git("worktree", "list", "--porcelain").stdout
        self.assertIn("worktree " + str(worktree), entries)
        self.assertIn("prunable", entries)
        # Its own Git paths cannot be inspected: absence is not proof of idle operation state.
        with self.assertRaises(FileNotFoundError):
            self.git("rev-parse", "--git-path", "rebase-merge", cwd=worktree)
        # Retain/report the exact metadata entry: no global prune in this sandbox.
        self.assertIn(str(worktree), self.git("worktree", "list", "--porcelain").stdout)


if __name__ == "__main__":
    unittest.main()
