"""Offline pack structure and budgets; executable Git scenarios live in test_git.py."""
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

    def test_verify_harness_reference(self):
        directory = ROOT / "skills/kstack-setup"
        reference = "references/verify-harness.md"
        harness = directory / reference
        self.assertTrue(harness.is_file())
        self.assertIn("`" + reference + "`", (directory / "SKILL.md").read_text())
        self.assertLessEqual(len(harness.read_bytes()), 720)

    def test_finish_and_execute_have_distinct_boundaries(self):
        execute = (ROOT / "skills/kstack-execute/SKILL.md").read_text()
        finish = (ROOT / "skills/kstack-finish/SKILL.md").read_text()
        self.assertIn("Stop before publishing", execute)
        self.assertIn("PR → green → merge → deploy → cleanup → local sync", finish)

    def test_dispatch_models_path_resolves(self):
        reference = ROOT / "skills/kstack/references/dispatch.md"
        paths = re.findall(r"`([^`]+/kstack-models)`", reference.read_text())
        self.assertEqual(len(paths), 1)
        models = (reference.parent / paths[0]).resolve()
        self.assertEqual(models, (ROOT / "skills/kstack-setup/scripts/kstack-models").resolve())
        self.assertTrue(models.is_file())

    def test_finish_stage_order(self):
        finish = (ROOT / "skills/kstack-finish/SKILL.md").read_text()
        titles = ["Preflight", "Open/update PR", "Make green", "Merge",
                  "Deploy/verify", "Clean and sync"]
        positions = [finish.index("%d. **%s.**" % (i, title))
                     for i, title in enumerate(titles, 1)]
        self.assertEqual(positions, sorted(positions))

    def test_finish_target_set(self):
        finish = (ROOT / "skills/kstack-finish/SKILL.md").read_text()
        targets = re.findall(r"^- `([^`]+)`: .+$", finish, re.M)
        self.assertEqual(set(targets), {"pr-green", "merged", "complete", "deployed"})

    def test_finish_permissions_remain_user_owned(self):
        finish = (ROOT / "skills/kstack-finish/SKILL.md").read_text()
        for clause in ("user-config", "finish.allow_merge=true", "finish.allow_deploy=true",
                       "repo cannot authorize"):
            with self.subTest(clause=clause):
                self.assertIn(clause, finish.casefold())

    def test_no_saved_artifact_directives_across_pack(self):
        forbidden = (r"(?i)(?:keep|load|include) (?:a |the |shared )*durable (?:resource )?manifest",
                     r"(?i)(?:save|saving|retain|retaining) (?:the )?evidence outside",
                     r"(?i)state table outside the repo", r"(?i)recovery manifest path",
                     r"(?i)(?:ask the agent to write|write a job-owned report file|evidence paths|and the artifact path)",
                     r"(?i)(?:full tables stay in the report|link only shareable evidence)",
                     r"(?i)Keep the report and evidence outside", r"(?i)recovery locations")
        for path in [ROOT / "README.md", *(ROOT / "skills").rglob("*.md")]:
            text = path.read_text()
            for pattern in forbidden:
                self.assertFalse(re.search(pattern, text), str(path) + ": forbidden retention directive")

    def test_no_archive_relocation_or_success_leftover_path_footer(self):
        for path in [ROOT / "README.md", *(ROOT / "skills").rglob("*.md")]:
            self.assertNotRegex(path.read_text(), r"(?i)(?:logs and notes are in|reports saved to|archive (?:the )?(?:logs|reports))")

    def test_skill_size_budgets(self):
        sizes = {name: len((ROOT / "skills" / name / "SKILL.md").read_bytes())
                 for name in NAMES}
        limits = {"kstack": 2830, "kstack-finish": 4050, "kstack-execute": 3300,
                  "kstack-setup": 2540, "kstack-plan": 1070, "kstack-debug": 860,
                  "kstack-review": 1640, "kstack-verify": 1370, "kstack-perf": 910,
                  "kstack-improve": 1370, "kstack-understand": 530}
        self.assertEqual(set(limits), NAMES)
        self.assertLessEqual(sum(sizes.values()), 21500)
        for name, limit in limits.items():
            self.assertLessEqual(sizes[name], limit, name)
        # Count every Markdown reference too: moving prose cannot evade the pack budget.
        prompt_bytes = sum(len(path.read_bytes()) for path in (ROOT / "skills").rglob("*.md"))
        self.assertLessEqual(prompt_bytes, 24500)
        self.assertLessEqual(len((ROOT / "skills/kstack-finish/references/cleanup.md").read_bytes()), 1540)
        self.assertLessEqual(len((ROOT / "skills/kstack/references/dispatch.md").read_bytes()), 1180)

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
