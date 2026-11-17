"""Offline pack contracts; executable Git scenarios live in test_git.py."""
import importlib.machinery
import importlib.util
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
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
                self.assertIn("# " + name + "\n", body)
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
                for ref in re.findall(r"`((?:\.\./|references/)[^`]+)`", text):
                    if "<" not in ref:  # The router also documents a sibling path template.
                        self.assertTrue((directory / ref).is_file(), ref)

    def test_exact_skill_names_and_router_coverage(self):
        router = (ROOT / "skills/kstack/SKILL.md").read_text()
        readme = (ROOT / "README.md").read_text()
        for name in NAMES - {"kstack"}:
            self.assertIn(name, router)
            self.assertIn("[" + name + "](skills/" + name + "/SKILL.md)", readme)
        for path in [ROOT / "README.md", *(ROOT / "skills").rglob("*.md")]:
            text = path.read_text()
            for name in re.findall(r"\bkstack(?:-[a-z]+)*\b", text):
                self.assertIn(name, NAMES | {"kstack-models", "kstack-git"}, str(path))
            self.assertNotRegex(text, r"\b(?:Finish|Execute|Setup)\b")
            for ref in re.findall(r"\]\(([^)]+)\)", text):
                if "://" not in ref:
                    self.assertTrue((path.parent / ref.split("#")[0]).is_file(), ref)

    def test_git_subcommand_links(self):
        script = ROOT / "skills/kstack-finish/scripts/kstack-git"
        loader = importlib.machinery.SourceFileLoader("pack_git", str(script))
        spec = importlib.util.spec_from_loader("pack_git", loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        choices = next(action.choices for action in module.build_parser()._actions
                       if isinstance(action.choices, dict))
        mentions = set()
        for path in [ROOT / "README.md", *(ROOT / "skills").rglob("*.md")]:
            for sub in re.findall(r"\bkstack-git\s+([a-z][a-z-]*)", path.read_text()):
                self.assertIn(sub, choices, str(path))
                mentions.add(sub)
        self.assertEqual(mentions, set(choices))

    def test_finish_and_execute_have_distinct_boundaries(self):
        execute = (ROOT / "skills/kstack-execute/SKILL.md").read_text()
        finish = (ROOT / "skills/kstack-finish/SKILL.md").read_text()
        self.assertIn("Stop before publishing", execute)
        self.assertIn("PR → green → merge → deploy → cleanup → local sync", finish)


class ContractBase(unittest.TestCase):
    """Check written safeguards, not autonomous workflow behavior."""

    @classmethod
    def setUpClass(cls):
        cls.skills = {name: (ROOT / "skills" / name / "SKILL.md").read_text()
                      for name in NAMES}
        cls.finish = cls.skills["kstack-finish"]
        cls.cleanup = (ROOT / "skills/kstack-finish/references/cleanup.md").read_text()
        cls.efficiency = (ROOT / "skills/kstack-finish/references/efficiency.md").read_text()
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
        return self.finish.split("%d. **%s.**" % (number, title), 1)[1].split("\n", 1)[0]


class FinishContractTests(ContractBase):
    def test_dispatch_reuses_only_matching_gate_evidence(self):
        # Written policy contracts, not a scheduler simulation or runtime speed proof.
        self.require(self.finish, "Then read `references/efficiency.md`")
        self.require(self.execute, "Follow `../kstack-finish/references/efficiency.md`")
        self.require(self.efficiency, "Before dispatch record lane, exact base/head, scope, commands",
                     "environment/toolchain, provenance and result in chat",
                     "Reuse only matching PASS or justified N/A")

    def test_complete_evidence_allocates_zero_new_resources(self):
        self.require(self.efficiency, "Complete evidence needs zero new agents, worktrees or gates")

    def test_one_missing_lane_does_not_restart_the_swarm(self):
        self.require(self.efficiency, "otherwise run only missing lanes")
        self.require(self.execute, "Missing evidence gets one retry, then a gap", "N/A needs reason")

    def test_stale_or_unproven_evidence_cannot_pass(self):
        self.require(self.efficiency, "Unproven provenance", "invalidates reuse")
        for invalidation in ("base", "queue", "head", "commands", "config", "lockfile",
                             "toolchain", "environment"):
            self.assertIn(invalidation, self.efficiency.split("or changed ", 1)[1]
                          .split(" invalidates reuse", 1)[0].split("/"))
        self.require(self.efficiency, "Reuse only matching PASS or justified N/A")

    def test_shared_gates_preserve_independent_audit_judgment(self):
        self.require(self.efficiency, "One gate owner runs full required gates once",
                     "per revision/environment", "reviewers run focused probes, not duplicate suites")
        self.require(self.execute, "rerun gates and affected/failed scenarios", "full swarm within budget")

    def test_task_review_and_integration_audit_are_separate_evidence(self):
        review = self.skills["kstack-review"]
        task = review.split("- **Task:**", 1)[1].split("\n", 1)[0]
        audit = review.split("- **Audit:**", 1)[1].split("\n", 1)[0]
        self.require(task, "one task's diff against acceptance", "task checks/lint")
        self.require(audit, "at frozen head", "what task reviews cannot", "cross-task interactions",
                     "integration edits", "unreviewed changes", "request scope/regressions",
                     "don't rerun suites")
        self.require(self.execute, "task review at frozen base/head", "| Audit | kstack-review |")
        self.assertNotIn("audit reuse", self.execute)
        self.require(self.efficiency, "Task reviews (unreviewed work: one task) and the frozen-head audit",
                     "separate nonimplementers", "neither replaces the other")

    def test_known_repairs_are_batched_before_a_new_frozen_head(self):
        self.require(self.execute, "every started agent/task and known repair before freezing head",
                     "one swarm repair round through steps 2–3, batching all lanes' findings")
        self.require(self.stage(3, "Make green"), "Batch proven failures through fixer")

    def test_small_change_reuse_is_lane_specific_and_fails_closed(self):
        self.require(self.efficiency, "small repair/rebase heads keep only non-gate results",
                     "the old→new diff provably cannot reach")
        self.require(self.execute, "one independent verifier", "justify reuse per lane")

    def test_handoffs_carry_unresolved_evidence_not_reasoning(self):
        self.require(self.shared, "Hand off unresolved findings/evidence, not reasoning/transcripts")

    def test_watcher_and_concurrency_have_resource_limits(self):
        self.require(self.finish, "One PR watcher", "bounded backoff", "honor rate limits",
                     "One deadline across waits/resumes/new heads", "recheck new heads, never reset deadline")
        self.require(self.efficiency, "Cap aggregate concurrency by available CPU/memory",
                     "sequence if unknown", "Concurrent stateful lanes isolate checkouts/ports/data/builds")
        self.require(self.shared, "foreground agents sequentially", "no hidden background agents")

    def test_efficiency_never_reuses_destructive_safety_checks(self):
        self.require(self.efficiency, "Never reuse destructive-action safety checks",
                     "freshly recheck `cleanup.md`")

    def test_optional_ci_tuning_is_measured_and_separately_authorized(self):
        self.require(self.readme, "https://x.com/owengretzinger/status/2116291924219060319",
                     "do not automatically change CI", "No paid or larger runners",
                     "without explicit consent", "benchmarking equivalent checks",
                     "Run independent lint, typecheck, build and test jobs concurrently",
                     "available CPU and memory budget", "Match aggregate task and test-worker concurrency",
                     "untrusted PRs must not write trusted caches", "A cache is never verification evidence",
                     "failing closed on unknowns, missing history or errors",
                     "Full required gates at head remain mandatory", "full main/nightly safety nets",
                     "without bypass or `--no-verify`", "never main, postmerge or shared runs")

    def test_stage_order_and_no_premature_cleanup(self):
        titles = ["Preflight", "Open/update PR", "Make green", "Merge",
                  "Deploy/verify", "Clean and sync"]
        positions = [self.finish.index("%d. **%s.**" % (i, title))
                     for i, title in enumerate(titles, 1)]
        self.assertEqual(positions, sorted(positions))
        self.require(self.stage(4, "Merge"), "never `--delete-branch`")
        self.require(self.stage(6, "Clean and sync"), "references/cleanup.md", "every return, even blocked")
        self.require(self.cleanup, "Source deletion waits for confirmed merge and all target gates")
        self.require(self.cleanup, "confirmed merge and all target gates")

    def test_targets_have_distinct_outcomes(self):
        rows = dict(re.findall(r"^- `([^`]+)`: (.+)$", self.finish, re.M))
        self.assertEqual(set(rows), {"pr-green", "merged", "complete", "deployed"})
        self.require(rows["pr-green"], "stop before merge", "retain source work")
        self.require(rows["merged"], "postmerge gates", "automatic delivery", "no manual deploy")
        self.require(rows["complete"], "every affected app", "diff/recipe proof")
        self.require(rows["deployed"], "at least one actual deploy")

    def test_preflight_permissions_and_already_merged_resume(self):
        self.require(self.finish, "request, project, user, then `complete`", "Targets are not permission",
                     "user-config", "finish.allow_merge=true", "finish.allow_deploy=true",
                     "Repo cannot authorize", "destructive migrations need separate consent")
        self.require(self.stage(1, "Preflight"), "base/head", "workers/locks", "apps/shared/schema/config",
                     "credentials", "environment/revision", "dependency/migration order",
                     "block before merge", "merged resumes recover verified head/merge proof",
                     "skip publishing/merging")

    def test_verification_watch_and_repair_are_bounded(self):
        self.require(self.stage(2, "Open/update PR"), "../kstack-execute/SKILL.md", "verification swarm")
        self.require(self.efficiency, "exact base/head", "Reuse only matching PASS or justified N/A")
        self.require(self.stage(3, "Make green"), "current-head checks/reviews/approvals",
                     "proven failures", "independent reviewer", "kstack-execute repair verification",
                     "change/base/infra/flaky", "one infra/flaky rerun", "never relabel red as green",
                     "untrusted data", "owned user-controlled", "--force-with-lease=<ref>:<expected-sha>",
                     "Reread base/head", "never bypass protection")
        self.require(self.finish, "default 30, positive nonboolean integer", "One deadline across waits/resumes/new heads",
                     "finish.max_fix_rounds", "bounds all repairs", "PENDING", "BLOCKED",
                     "NO_CI with local proof", "never CI-green", "expected missing workflows block")
        self.require(self.execute, "one swarm repair round", "one independent verifier",
                     "rerun gates and affected/failed scenarios", "full swarm within budget")

    def test_merge_and_postmerge_evidence_are_separate(self):
        self.require(self.stage(4, "Merge"), "PR gates and permission", "base/head movement, including queues",
                     "allowed-method", "kstack-git merge-pr", "--match-head <verified-head>", "API-confirmed merge",
                     "map verified head to merge SHA", "ancestry on fetched base",
                     "API commit mapping, not similar trees/messages")
        self.require(self.stage(5, "Deploy/verify"), "exact merge-SHA postmerge checks",
                     "not PR green/previews/old builds", "bounded follow-up PRs", "never rewrite history")

    def test_delivery_requires_component_and_environment_evidence(self):
        self.require(self.stage(5, "Deploy/verify"), "authorized recipes", "dependency order",
                     "automatic delivery", "environment/build/revision proof", "health/schema/API",
                     "frontend browser smoke", "client/API integration")
        self.require(self.finish, "No deployable changes needs diff/recipe proof",
                     "Missing requirements block before merge", "Complete requires target gates")

    def test_cleanup_ownership_remains_judgment(self):
        self.require(self.cleanup, "Never delete base/shared/unmerged/unrelated resources",
                     "retain advanced/unintegrated refs")
        self.require(self.execute, "Shared rules: read `../kstack/SKILL.md` first")
        self.require(self.shared, "Only kstack-finish publishes/merges/deploys", "Retain unmerged source/unique code",
                     "Preserve product files, application logs/config/docs and user data")

    def test_conversation_inventory_records_resources_and_ownership_as_created(self):
        self.require(self.finish, "in chat as created/adopted", "common Git directory", "job, path/ref, role",
                     "type/hash/entry set", "ownership, integration proof, disposition",
                     "Remote ownership follows `references/cleanup.md`", "duplicates/origins/scopes/file or absence",
                     "after authorized changes", "kstack-git snapshot-branch-config", "digest at creation")
        self.require(self.cleanup, "job/remote/ref/SHA push proof or explicit adoption")
        self.require(self.shared, "inventory/results in conversation/stdout, never files")
        self.require(self.execute, "inventory resources under kstack-finish as created")

    def test_resume_and_legacy_adoption_are_bounded(self):
        self.require(self.cleanup, "creation/adoption inventory", "Legacy needs prior proof or bounded user scope",
                     "repo/resources/ownership", "never Projects-wide", "ownership alone is not integration/content safety")
        self.require(self.finish, "Remote ownership follows `references/cleanup.md`")
        self.require(self.cleanup, "Failed/uncertain checks mean retain and report partial",
                     "ownership alone is not integration/content safety")
        self.require(self.shared, "conversation plus actual Git/PR state, not saved logs")

    def test_per_role_integration_and_exact_merge_chain(self):
        self.require(self.execute, "reviewed final worker tip after rebase", "integration SHA",
                     "git merge-base --is-ancestor <worker-tip> <frozen-head>", "not PR-head equality",
                     "Retain advanced/unintegrated refs", "Renew proof after rewrites or retain")
        self.require(self.cleanup, "verified PR-to-merge proof", "workers need reviewed-tip ancestry",
                     "delivery-to-PR-to-merge chain", "API commit mapping", "unique commits",
                     "Detached verifiers must match recorded SHA")

    def test_delivery_and_cleanup_have_separate_status_and_recovery(self):
        self.require(self.finish, "Separate target success from source/temporary cleanup",
                     "pr-green source retention is intentional", "Complete requires target gates and required cleanup/sync")
        self.require(self.shared, "Retain unmerged source/unique code", "unsafe cleanup is partial")

    def test_script_calls_and_local_sync_order(self):
        self.require(self.stage(6, "Clean and sync"), "Follow `references/cleanup.md`")
        self.require(self.cleanup, "digest in chat", "Only done/absent counts as cleaned", "Quiesce writers",
                     "retained/error is partial", "inventory proofs, never a newly observed tip")
        calls = ["scratch-digest", "delete-scratch", "delete-remote-branch", "remove-worktree",
                 "delete-local-branch", "sync-local"]
        positions = [self.cleanup.index("kstack-git " + call) for call in calls]
        self.assertEqual(positions, sorted(positions))

    def test_setup_and_readme_preserve_migration_and_recipe_contract(self):
        for field in ("name", "paths", "depends_on", "environment", "mode", "apply", "verify"):
            self.require(self.setup, "`" + field + "`")
        self.require(self.setup, "`auto` or `manual`", "manual command", "identified merge-triggered recipe",
                     "finish.deploy_checks", "verification evidence fallback, not an apply recipe",
                     "helper does not validate project recipes", "kstack-finish preflight", "not guesses")
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
                     "No saved logs/notes/reports/plans/state", "redirect/tee", "requested changes remain allowed")

    def test_no_saved_artifact_directives_across_pack(self):
        forbidden = (r"(?i)(?:keep|load|include) (?:a |the |shared )*durable (?:resource )?manifest",
                     r"(?i)(?:save|saving|retain|retaining) (?:the )?evidence outside",
                     r"(?i)state table outside the repo", r"(?i)recovery manifest path",
                     r"(?i)(?:ask the agent to write|write a job-owned report file|evidence paths|and the artifact path)",
                     r"(?i)(?:full tables stay in the report|link only shareable evidence)",
                     r"(?i)Keep the report and evidence outside", r"(?i)recovery locations")
        for name, text in {**self.skills, "cleanup": self.cleanup, "efficiency": self.efficiency,
                           "README": self.readme}.items():
            for pattern in forbidden:
                self.assertFalse(re.search(pattern, text), name + ": forbidden retention directive")

    def test_every_settled_return_cleans_diagnostic_scratch(self):
        self.require(self.shared, "Before every settled return", "stop exact owned temporary PIDs",
                     "capture results", "delete safe owned scratch/disposable verifiers", "read back absence",
                     "never waits for merge/delivery", "unsafe cleanup is partial with exact blocker")
        self.require(self.finish, "every return, even blocked")
        self.require(self.execute, "shared cleanup safeguards/readback")

    def test_no_archive_relocation_or_success_leftover_path_footer(self):
        self.require(self.shared, "archive relocation", "leftover logs-path footer",
                     "Limit output", "exact owned overflow logs", "never sweep caches")
        self.require(self.finish, "Complete requires target gates and required cleanup/sync")
        for text in (*self.skills.values(), self.cleanup, self.efficiency, self.readme):
            self.assertNotRegex(text, r"(?i)(?:logs and notes are in|reports saved to|archive (?:the )?(?:logs|reports))")

    def test_stdout_collection_resume_and_direct_pr_results(self):
        self.require(self.shared, "require assignment stdout", "retry collection",
                     "Missing results are verification gaps, never report files",
                     "conversation plus actual Git/PR state, not saved logs")
        self.require(self.finish, "preserve existing descriptions except direct verification results",
                     "then read back")

    def test_verify_returns_outcomes_and_deletes_temporary_captures(self):
        self.require(self.verify, "return revision-bound outcomes in chat", "Avoid captures",
                     "shared owned scratch rules", "shared cleanup safeguards/readback",
                     "Stop only your processes", "in stdout/chat", "Required behavior that cannot run",
                     "wrong interaction method or inconclusive evidence is BLOCKED")

    def test_skill_size_budgets(self):
        sizes = {name: len(text.encode()) for name, text in self.skills.items()}
        limits = {"kstack": 3300, "kstack-finish": 4200, "kstack-execute": 3300,
                  "kstack-setup": 2600, "kstack-plan": 920, "kstack-debug": 820,
                  "kstack-review": 1280, "kstack-verify": 1160, "kstack-perf": 940,
                  "kstack-improve": 680, "kstack-understand": 550}
        self.assertEqual(set(limits), NAMES)
        self.assertLessEqual(sum(sizes.values()), 21500)
        for name, limit in limits.items():
            self.assertLessEqual(sizes[name], limit, name)
        # Count every Markdown reference too: moving prose cannot evade the pack budget.
        prompt_bytes = sum(len(path.read_bytes()) for path in (ROOT / "skills").rglob("*.md"))
        self.assertLessEqual(prompt_bytes, 24500)
        self.assertLessEqual(len(self.cleanup.encode()), 1600)

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


if __name__ == "__main__":
    unittest.main()
