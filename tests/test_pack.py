"""Offline distribution and prompt-contract checks, not live GitHub/deploy proof."""
import re
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
                       "Fast-forward the local base", "without reset", "`git branch -d`",
                       "`-D` only with exact API merge proof, unchanged recorded tip",
                       "no unmerged commits beyond the verified PR", "No broad prune, clean, or reset",
                       "Read back local refs, `git worktree list`, remote refs",
                       "cleanup skipped", "evidence outside removed worktrees"):
            self.assertIn(phrase, cleanup)
        self.assertIn("Preserve the unmerged delivery branch and worktree for Finish", self.execute)
        self.assertIn("only its clean, idle, disposable verifier worktrees", self.execute)
        self.assertIn("Only Finish cleans delivery resources", self.shared)

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


if __name__ == "__main__":
    unittest.main()
