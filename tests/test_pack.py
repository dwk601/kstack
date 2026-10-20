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


class ContractBase(unittest.TestCase):
    """Check written safeguards, not autonomous workflow behavior."""

    @classmethod
    def setUpClass(cls):
        cls.skills = {name: (ROOT / "skills" / name / "SKILL.md").read_text()
                      for name in NAMES}
        cls.finish = cls.skills["kstack-finish"]
        cls.shared = cls.skills["kstack"]
        cls.execute = cls.skills["kstack-execute"]
        cls.setup = cls.skills["kstack-setup"]
        cls.verify = cls.skills["kstack-verify"]
        cls.readme = (ROOT / "README.md").read_text()

    def require(self, text, *clauses):
        for clause in clauses:
            with self.subTest(clause=clause):
                self.assertTrue(clause in text, "Missing contract: " + clause)

    def stage(self, number, title):
        return self.finish.split("## %d. %s\n" % (number, title), 1)[1].split("\n## ", 1)[0]


class FinishContractTests(ContractBase):
    def test_stage_order_and_no_premature_cleanup(self):
        titles = ["Preflight", "Publish and verify", "Watch and repair",
                  "Merge and postmerge gates", "Apply and verify delivery", "Cleanup", "Report"]
        positions = [self.finish.index("## %d. %s\n" % (i, title))
                     for i, title in enumerate(titles, 1)]
        self.assertEqual(positions, sorted(positions))
        self.require(self.stage(4, titles[3]), "never `--delete-branch`")
        self.require(self.stage(6, titles[5]), "after confirmed merge and ALL target gates",
                     "never green PR/queue/pending/failed deploy", "scratch cleanup is independent")

    def test_targets_have_distinct_outcomes(self):
        rows = {line.split("|")[1].strip(): line for line in self.finish.splitlines()
                if line.startswith("| `")}
        self.assertEqual(set(rows), {"`pr-green`", "`merged`", "`complete` (default)", "`deployed`"})
        self.require(rows["`pr-green`"], "never merge", "Retain delivery, integration and workers")
        self.require(rows["`merged`"], "postmerge gates", "no manual deploy")
        self.require(rows["`complete` (default)"], "every affected app", "proof of no deployable changes")
        self.require(rows["`deployed`"], "at least one actual deploy")

    def test_preflight_permissions_and_already_merged_resume(self):
        self.require(self.finish, "request, project, user, then `complete`", "A target is not permission",
                     "literal user-config", "finish.allow_merge=true", "finish.allow_deploy=true",
                     "Repo cannot authorize", "merge-triggered auto-deploys",
                     "destructive migrations need separate consent")
        self.require(self.stage(1, "Preflight"), "repo/fork/head remote", "original base/head proof",
                     "skip publishing/remerging", "shared/config/schema/migrations", "credentials",
                     "dependency/migration order", "BLOCKED before merge", "merged resumes retain resources")

    def test_verification_watch_and_repair_are_bounded(self):
        self.require(self.stage(2, "Publish and verify"), "exact base/head", "verification swarm",
                     "Reuse valid evidence", "Never invent PASS")
        self.require(self.stage(3, "Watch and repair"), "default 30, positive nonboolean integer",
                     "one deadline across waits/resumes", "finish.max_fix_rounds", "bounds all repairs",
                     "one infra/flaky rerun", "fixer then reviewer", "Reject unsupported bot requests",
                     "single-verifier/full-swarm", "user-controlled", "Shared/uncertain ownership stops",
                     "--force-with-lease=<ref>:<expected-sha>", "reread base/head", "never bypass protection",
                     "PENDING", "BLOCKED", "retain source work", "NO_CI with local proof",
                     "Expected missing workflows are BLOCKED", "never CI-green")

    def test_merge_and_postmerge_evidence_are_separate(self):
        self.require(self.stage(4, "Merge and postmerge gates"), "permission/protection",
                     "reverify movement, including queues", "allowed method", "--match-head-commit <verified-head>",
                     "PENDING until MERGED/mergedAt/mergeCommit.oid proof", "invalid evidence blocks",
                     "git merge-base --is-ancestor <merge-sha> <base-ref>", "not necessarily tip",
                     "exact merge-SHA", "head_sha", "jobs/steps/conclusions/provider revisions",
                     "not PR green/newer base", "apply before dependent checks", "deadline/NO_CI",
                     "follow-up PRs", "never rewrite merged history", "rerun affected gates")

    def test_delivery_requires_component_and_environment_evidence(self):
        self.require(self.stage(5, "Apply and verify delivery"), "dependency order",
                     "merged only observes", "backend/frontend/apps separately", "migrations precede dependent code",
                     "Recheck manual permission/destructive consent", "health/schema/API",
                     "build identity/browser smoke", "client/API integration if both change",
                     "N/A needs diff/recipe proof", "missing recipes are BLOCKED",
                     "mapping to merge SHA", "provider steps/success/verification",
                     "Hooks, build alone, preview or old SHA are insufficient",
                     "All required gates must pass within deadline", "failures retain resources")

    def test_cleanup_requires_ownership_leases_and_readback(self):
        self.require(self.stage(6, "Cleanup"), "never base/shared/unmerged/unrelated",
                     "Retain advanced/unintegrated refs", "--force-with-lease=refs/heads/<branch>:<recorded-head>",
                     "git update-ref -d refs/heads/<branch> <expected-sha>", "`git branch -d` ancestry safety",
                     "lacks branch safety; proofs are mandatory", "Stale expected-old must reject",
                     "never retry new tip", "Never branch -D", "without reset",
                     "Read back refs/paths/worktree metadata/base/status", "uncertainty stays skipped")
        self.require(self.execute, "Preserve unmerged delivery branch/worktree")
        self.require(self.shared, "Only Finish publishes", "preserve unmerged source")

    def test_conversation_inventory_records_resources_and_ownership_as_created(self):
        self.require(self.finish, "in chat as created/adopted", "common Git directory", "job, path/ref, role",
                     "expected SHA", "type+hash/entry set", "ownership, integration proof, disposition",
                     "workers, fixes/follow-ups, detached verifiers and scratch",
                     "exact job remote/ref/SHA push proof or explicit adoption, not local names")
        self.require(self.shared, "ownership inventory in conversation/memory or stdout, never files")
        self.require(self.execute, "inventory resources under Finish as created")

    def test_resume_and_legacy_adoption_are_bounded(self):
        self.require(self.finish, "Resume only proven ownership", "otherwise retain",
                     "Legacy needs prior proof or explicit bounded user scope",
                     "repo/resources/ownership", "never Projects-wide", "Ownership is not integration/content safety")
        self.require(self.shared, "conversation plus actual Git/PR state, never saved logs")

    def test_per_role_integration_and_exact_merge_chain(self):
        self.require(self.execute, "reviewed final worker tip after rebase", "integration SHA",
                     "git merge-base --is-ancestor <worker-tip> <frozen-head>", "not PR-head equality",
                     "Retain advanced/unintegrated refs", "Renew proof after rewrites or retain")
        self.require(self.finish, "API commit mapping, not ancestry or similar trees/messages",
                     "worker-to-frozen delivery-to-verified PR-to-merge chain",
                     "workers need frozen-head ancestry and merge chain", "detached verifiers match SHA",
                     "unique commits outside chain")

    def test_worktree_cleanup_includes_ignored_and_missing_metadata_safety(self):
        self.require(self.stage(6, "Cleanup"), "clean, idle, unlocked, disposable",
                     "git status --porcelain --untracked-files=all --ignored", "unknown/changed content retains",
                     "immediately recheck status under quiescence", "git worktree remove <exact-path>",
                     "without --force", "never delete refs associated with", "git worktree list --porcelain",
                     "retain dirty/divergent base", "Missing path with metadata", "never global prune",
                     "Path absence with metadata is not done")

    def test_local_cas_requires_all_worktree_operation_state_checks(self):
        self.require(self.finish, "Inspect ALL worktrees including main", "clean detached HEAD",
                     "git -C <worktree> rev-parse --git-path <marker>", "Resolve relative to that worktree and lstat",
                     "never assume common paths", "marker/symlink/operation/uninspectable state",
                     "defers local refs", "inspection/deletion/config/readback quiescent")
        for marker in ("rebase-merge", "rebase-apply", "BISECT_START", "MERGE_HEAD",
                       "CHERRY_PICK_HEAD", "REVERT_HEAD", "sequencer"):
            self.require(self.finish, "`" + marker + "`")

    def test_branch_config_cleanup_requires_unchanged_owned_section_and_readback(self):
        self.require(self.finish, "after authorized updates", "exact section, duplicates, origins/scopes/file or absence",
                     "Before CAS match exact branch.<name> section to Inventory snapshot",
                     "not fresh observation/regex/prefix", "Only after successful CAS and ref-absence readback",
                     "recheck unchanged owned section", "git config --file <owning-file> --remove-section branch.<name>",
                     "Never unrelated/shared/unowned/global/included config", "lost quiescence mean retain/partial",
                     "Failed CAS forbids config removal", "Absent sections are idempotent after readback",
                     "absent refs with config need prior CAS proof", "exact config section absence across origins/scopes",
                     "not just upstream keys")

    def test_artifact_cleanup_requires_exact_untracked_identity(self):
        self.require(self.finish, "exact inventoried ephemeral type+hash", "literal-pathspec",
                     "git ls-files --error-unmatch -- <relative-path>", "every file, including directory contents",
                     "Tracked forbids deletion", "distinguish untracked from Git/path errors",
                     "exact owned temporary root, not merely TMPDIR", "lstat every component",
                     "no symlinks/ancestor escape", "Recheck hashes immediately before unlink",
                     "exact unchanged entry sets/all hashes", "no extra/changed entries/symlinks; otherwise retain",
                     "Never patterns, git clean, broad prune/reset or forced worktrees")
        self.require(self.shared, "Preserve application logs/config/docs, product files and user data")

    def test_delivery_and_cleanup_have_separate_status_and_recovery(self):
        self.require(self.stage(7, "Report"), "delivery success/pending/blocked",
                     "delivery-resource cleanup complete/partial/not-started", "diagnostic cleanup complete/partial",
                     "Target is not cleanup status", "Partial cleanup is not overall complete",
                     "pr-green retention is intentional not-started/not requested, not failure")
        self.require(self.shared, "Retain unmerged source branches/worktrees and unique code")

    def test_setup_and_readme_preserve_migration_and_recipe_contract(self):
        for field in ("name", "paths", "depends_on", "environment", "mode", "apply", "verify"):
            self.require(self.setup, "`" + field + "`")
        self.require(self.setup, "`auto` or `manual`", "Manual command", "identified merge-triggered recipe",
                     "finish.deploy_checks", "verification evidence fallback, not an apply recipe",
                     "helper does not validate project recipes", "Finish preflight", "not guesses")
        for text in (self.setup, self.readme):
            self.require(text, "pr-green", "`complete`", "reinstalling never overrides",
                         "user-owned permissions", "npx skills add ./kstack")
        self.require(self.readme, "not live proof of GitHub merging or deployment")


class RunArtifactContractTests(ContractBase):
    def test_all_eleven_skills_inherit_no_saved_run_artifacts(self):
        self.assertEqual(len(self.skills), 11)
        for name, text in self.skills.items():
            if name != "kstack":
                self.require(text, "Shared rules: read `../kstack/SKILL.md` first")
        self.require(self.shared, "No saved run artifacts", "never files inside or outside repo",
                     "No logs, notes, reports, plans, manifests, state files", "redirect/tee",
                     "requested product/config/docs changes are allowed")

    def test_no_saved_artifact_directives_across_pack(self):
        forbidden = (r"(?i)(?:keep|load|include) (?:a |the |shared )*durable (?:resource )?manifest",
                     r"(?i)(?:save|saving|retain|retaining) (?:the )?evidence outside",
                     r"(?i)state table outside the repo", r"(?i)recovery manifest path",
                     r"(?i)(?:ask the agent to write|write a job-owned report file|evidence paths|and the artifact path)",
                     r"(?i)(?:full tables stay in the report|link only shareable evidence)",
                     r"(?i)Keep the report and evidence outside", r"(?i)recovery locations")
        for name, text in {**self.skills, "README": self.readme}.items():
            for pattern in forbidden:
                self.assertFalse(re.search(pattern, text), name + ": forbidden retention directive")

    def test_every_settled_return_cleans_diagnostic_scratch(self):
        self.require(self.shared, "Before every settled return", "success, failure, blocked, pending, timeout, pr-green, handoff",
                     "stop temporary processes by exact PID first", "Capture results in conversation",
                     "delete exact owned scratch/disposable verifier worktrees", "read back absence",
                     "never waits for merge/delivery", "Unsafe deletion means cleanup partial with exact blocker")
        self.require(self.finish, "Shared scratch cleanup is independent")
        self.require(self.execute, "shared scratch cleanup under Finish safety/readback")

    def test_no_archive_relocation_or_success_leftover_path_footer(self):
        self.require(self.shared, "archive/cache relocation", "leftover logs-path footer",
                     "Limit output", "exact tool-generated overflow logs", "never sweep caches")
        self.require(self.finish, "Partial cleanup is not overall complete")
        for text in (*self.skills.values(), self.readme):
            self.assertNotRegex(text, r"(?i)(?:logs and notes are in|reports saved to|archive (?:the )?(?:logs|reports))")

    def test_stdout_collection_resume_and_direct_pr_results(self):
        self.require(self.shared, "require assignment stdout", "Retry collection/request stdout summary",
                     "still missing means verification gap, never report files",
                     "conversation plus actual Git/PR state, never saved logs")
        self.require(self.finish, "preserve existing descriptions except kstack verification",
                     "direct results, no report links/paths", "Read back")

    def test_verify_returns_outcomes_and_deletes_temporary_captures(self):
        self.require(self.verify, "return revision-bound outcomes in chat", "Avoid captures",
                     "shared owned scratch rules", "shared cleanup and Finish safety/readback rules",
                     "Stop only your processes", "in stdout/chat", "Required behavior that cannot run",
                     "wrong interaction method or inconclusive evidence is BLOCKED")

    def test_remote_absence_is_read_before_delete_and_after_failure(self):
        self.require(self.finish, "git ls-remote --heads <head-remote> refs/heads/<branch>",
                     "Only successful empty output proves absence", "don't delete absent refs",
                     "After failed deletion/lease reread", "proven absent succeeds, else retain",
                     "Errors never prove absence")

    def test_skill_size_budgets(self):
        sizes = {name: len(text.encode()) for name, text in self.skills.items()}
        self.assertLessEqual(sum(sizes.values()), 27560)
        for name, limit in {"kstack": 4000, "kstack-finish": 10000,
                            "kstack-execute": 4500, "kstack-setup": 4500}.items():
            self.assertLessEqual(sizes[name], limit, name)

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
