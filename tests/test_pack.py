"""Offline distribution checks; workflow correctness still needs a real run."""
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


if __name__ == "__main__":
    unittest.main()
