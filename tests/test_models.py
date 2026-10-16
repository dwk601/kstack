"""Tests for skills/kstack-setup/scripts/kstack-models. Stdlib only.

Run: python3 -m unittest discover -s tests
"""
import copy
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True  # keep the extensionless script from leaving __pycache__ in skills/
SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "kstack-setup" / "scripts" / "kstack-models"
_loader = importlib.machinery.SourceFileLoader("kstack_models", str(SCRIPT))
_spec = importlib.util.spec_from_loader("kstack_models", _loader)
km = importlib.util.module_from_spec(_spec)
_loader.exec_module(km)

BASE = {
    "models": {
        "deep": {"cli": "codex", "model": "gpt-deep", "effort": "high", "args": ["--search"]},
        "critic": {"cli": "pi", "model": "prov/critic-1", "effort": "high"},
        "builder": {"cli": "pi", "model": "prov/builder-1", "effort": "medium"},
        "builder2": {"cli": "pi", "model": "prov/builder-2", "effort": "low", "args": ["--tools", "read"]},
        "checker": {"cli": "pi", "model": "prov/checker-1", "effort": "high"},
    },
    "roles": {
        "planner": "deep",
        "plan_critic": "critic",
        "workers": ["builder", "builder2"],
        "reviewer": "checker",
        "security_reviewer": "critic",
        "verifiers": ["critic", "checker", "deep"],
        "fixer": "builder",
    },
    "execution": {"max_fails": 3},
    "finish": {"target": "pr-green", "max_fix_rounds": 3, "allow_merge": False, "allow_deploy": False},
}


def cfg(**changes):
    """Deep copy of BASE; `a__b=v` sets c[a][b], value DELETE removes the key."""
    c = copy.deepcopy(BASE)
    for path, value in changes.items():
        keys = path.split("__")
        node = c
        for k in keys[:-1]:
            node = node[k]
        if value is DELETE:
            node.pop(keys[-1], None)
        else:
            node[keys[-1]] = value
    return c


DELETE = object()


def run_cli(config, *args, env_extra=None):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "config.json"
        path.write_text(config if isinstance(config, str) else json.dumps(config))
        env = dict(os.environ, KSTACK_CONFIG=str(path), CODEX_HOME=str(Path(d) / "nocodex"))
        env.update(env_extra or {})
        return subprocess.run([sys.executable, str(SCRIPT)] + list(args),
                              capture_output=True, text=True, env=env, timeout=60)


class ProblemsTest(unittest.TestCase):
    def test_base_is_valid(self):
        self.assertEqual(km.problems(cfg()), [])

    def test_example_config_is_shape_valid(self):
        example = SCRIPT.parent.parent / "references" / "config.example.json"
        self.assertEqual(km.problems(json.loads(example.read_text())), [])

    def test_allow_flags_must_be_boolean_when_present(self):
        for key in ("allow_merge", "allow_deploy"):
            for bad in ("false", "true", 0, 1, None, [], {}):
                errs = km.problems(cfg(**{"finish__" + key: bad}))
                self.assertIn("finish.%s: must be true or false" % key, errs, (key, bad))
            for good in (True, False):
                self.assertEqual(km.problems(cfg(**{"finish__" + key: good})), [])

    def test_allow_flags_missing_is_fine(self):
        self.assertEqual(km.problems(cfg(finish__allow_merge=DELETE, finish__allow_deploy=DELETE)), [])

    def test_counts_must_be_positive_non_boolean_ints(self):
        for path, label in (("execution__max_fails", "execution.max_fails"),
                            ("finish__max_fix_rounds", "finish.max_fix_rounds")):
            msg = "%s: must be a positive integer" % label
            for bad in (True, False, 0, -1, 1.5, 2.0, "3", None, DELETE):
                self.assertIn(msg, km.problems(cfg(**{path: bad})), (path, bad))
            for good in (1, 3, 50):
                self.assertEqual(km.problems(cfg(**{path: good})), [], (path, good))

    def test_malformed_sections_reported_without_exceptions(self):
        for key in ("models", "roles", "execution", "finish"):
            for bad in ([], "x", 3, True):
                errs = km.problems(cfg(**{key: bad}))
                self.assertIn("%s: must be an object" % key, errs, (key, bad))

    def test_malformed_preset_reported(self):
        errs = km.problems(cfg(models__critic="prov/critic-1"))
        self.assertIn("model critic: must be an object", errs)
        errs = km.problems(cfg(models__critic=["x"]))
        self.assertIn("model critic: must be an object", errs)

    def test_malformed_role_values_reported(self):
        msg = "role workers: must be a preset name or a list of preset names"
        for bad in ([{"name": "builder"}], [["builder"]], 7, True, ["builder", None]):
            errs = km.problems(cfg(roles__workers=bad))
            self.assertIn(msg, errs, bad)
        self.assertIn("role workers: not set", km.problems(cfg(roles__workers=[])))
        self.assertIn("role fixer: unknown model 'nope'", km.problems(cfg(roles__fixer="nope")))

    def test_target_still_validated(self):
        self.assertIn("finish.target: must be pr-green, merged, or deployed",
                      km.problems(cfg(finish__target="shipped")))
        self.assertEqual(km.problems(cfg(finish__target=DELETE)), [])

    def test_existing_preset_checks_kept(self):
        errs = km.problems(cfg(models__builder={"cli": "bash", "model": "", "effort": "huge", "args": "x"}))
        self.assertIn("model builder: cli must be one of pi, codex, claude, custom", errs)
        self.assertIn("model builder: missing model", errs)
        self.assertIn("model builder: args must be a list of strings", errs)
        errs = km.problems(cfg(models__critic__effort="huge"))
        self.assertIn("model critic: effort must be one of %s" % ", ".join(km.PI_EFFORTS), errs)


class ArgvTest(unittest.TestCase):
    def test_pi_interactive_and_oneshot(self):
        p = BASE["models"]["builder2"]
        self.assertEqual(km.argv(p), ["pi", "--model", "prov/builder-2:low", "--tools", "read"])
        self.assertEqual(km.argv(p, oneshot=True),
                         ["pi", "-p", "--no-session", "--model", "prov/builder-2:low", "--tools", "read"])

    def test_codex_args_before_exec(self):
        p = BASE["models"]["deep"]
        self.assertEqual(km.argv(p), ["codex", "--search", "-m", "gpt-deep", "-c", "model_reasoning_effort=high"])
        self.assertEqual(km.argv(p, oneshot=True),
                         ["codex", "--search", "exec", "-m", "gpt-deep", "-c", "model_reasoning_effort=high"])

    def test_claude_interactive_and_oneshot(self):
        p = {"cli": "claude", "model": "opus", "effort": "high", "args": ["--allowedTools", "Read"]}
        self.assertEqual(km.argv(p), ["claude", "--allowedTools", "Read", "--model", "opus", "--effort", "high"])
        self.assertEqual(km.argv(p, oneshot=True),
                         ["claude", "--allowedTools", "Read", "-p", "--model", "opus", "--effort", "high"])

    def test_custom_templates_fill_model_and_effort(self):
        p = {"cli": "custom", "model": "m-1", "effort": "low", "kind": "opencode",
             "command": ["opencode", "-m", "{model}", "--variant", "{effort}"],
             "oneshot": ["opencode", "run", "-m", "{model}", "--variant", "{effort}"]}
        self.assertEqual(km.argv(p), ["opencode", "-m", "m-1", "--variant", "low"])
        self.assertEqual(km.argv(p, oneshot=True), ["opencode", "run", "-m", "m-1", "--variant", "low"])

    def test_custom_without_oneshot_exits(self):
        p = {"cli": "custom", "model": "m", "effort": "low", "command": ["agent"]}
        with self.assertRaises(SystemExit):
            km.argv(p, oneshot=True)

    def test_configured_ids_never_rewritten(self):
        p = {"cli": "pi", "model": "OpenAI/GPT-X", "effort": "high"}
        self.assertEqual(km.argv(p), ["pi", "--model", "OpenAI/GPT-X:high"])


class MoreAgentsTest(unittest.TestCase):
    CUSTOM = {"cli": "custom", "model": "m", "effort": "low", "kind": "opencode",
              "command": ["opencode", "-m", "{model}"], "oneshot": ["opencode", "run", "-m", "{model}"]}

    def test_claude_and_custom_presets_validate(self):
        c = cfg(models__critic={"cli": "claude", "model": "opus", "effort": "max"},
                models__checker=self.CUSTOM)
        self.assertEqual(km.problems(c), [])

    def test_claude_effort_validated(self):
        errs = km.problems(cfg(models__critic={"cli": "claude", "model": "opus", "effort": "off"}))
        self.assertIn("model critic: effort must be one of %s" % ", ".join(km.CLAUDE_EFFORTS), errs)

    def test_custom_shape_validated(self):
        bad = dict(self.CUSTOM, command=[], oneshot="x", args=["--yolo"], kind=3)
        errs = km.problems(cfg(models__checker=bad))
        self.assertIn("model checker: command must be a non-empty list of strings", errs)
        self.assertIn("model checker: oneshot must be a non-empty list of strings", errs)
        self.assertIn("model checker: custom presets take no args; put them in command and oneshot", errs)
        self.assertIn("model checker: kind must be a string", errs)

    def test_cmd_forms_for_claude_and_custom(self):
        c = cfg(models__critic={"cli": "claude", "model": "opus", "effort": "high"}, models__checker=self.CUSTOM)
        self.assertEqual(run_cli(c, "cmd", "plan_critic").stdout.strip(), "claude --model opus --effort high")
        self.assertEqual(run_cli(c, "cmd", "plan_critic", "--oneshot").stdout.strip(),
                         "claude -p --model opus --effort high")
        r = run_cli(c, "cmd", "reviewer", "--herdr", "rev", "--pane", "p1")
        self.assertEqual(r.stdout.strip(), "herdr agent start rev --kind opencode --pane p1 -- -m m")
        r = run_cli(c, "cmd", "plan_critic", "--herdr", "c", "--pane", "p2")
        self.assertEqual(r.stdout.strip(), "herdr agent start c --kind claude --pane p2 -- --model opus --effort high")

    def test_uncatalogued_clis_are_noted_not_failed(self):
        c = cfg(models__critic={"cli": "claude", "model": "opus", "effort": "high"}, models__checker=self.CUSTOM)
        with mock.patch.object(km.subprocess, "run", side_effect=AssertionError("no catalog call expected")), \
                mock.patch.object(km.shutil, "which", return_value=None):
            c["models"]["builder"] = c["models"]["builder2"] = c["models"]["deep"] = self.CUSTOM
            bad, notes = km.availability(c)
        self.assertEqual(bad, [])
        self.assertEqual(notes, ["no model catalog for claude, custom; those presets not checked"])


class CmdCliTest(unittest.TestCase):
    def test_workers_pool_rotates_with_index(self):
        out = [run_cli(cfg(), "cmd", "workers", "--index", str(i)).stdout.strip() for i in range(4)]
        self.assertEqual(out, ["pi --model prov/builder-1:medium",
                               "pi --model prov/builder-2:low --tools read"] * 2)

    def test_verifier_lanes_rotate_across_pool_no_cap(self):
        out = [run_cli(cfg(), "cmd", "verifiers", "--index", str(i)).stdout.strip() for i in range(3)]
        self.assertEqual(out, ["pi --model prov/critic-1:high", "pi --model prov/checker-1:high",
                               "codex --search -m gpt-deep -c model_reasoning_effort=high"])

    def test_oneshot_and_herdr_forms(self):
        r = run_cli(cfg(), "cmd", "planner", "--oneshot")
        self.assertEqual(r.stdout.strip(), "codex --search exec -m gpt-deep -c model_reasoning_effort=high")
        r = run_cli(cfg(), "cmd", "reviewer", "--herdr", "rev", "--pane", "p1")
        self.assertEqual(r.stdout.strip(),
                         "herdr agent start rev --kind pi --pane p1 -- --model prov/checker-1:high")
        r = run_cli(cfg(), "cmd", "reviewer", "--herdr", "rev")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--herdr needs --pane", r.stderr)

    def test_invalid_config_exits_cleanly(self):
        cases = [
            "[1, 2]", '"text"', "null",
            json.dumps(cfg(models=[])), json.dumps(cfg(roles="x")),
            json.dumps(cfg(execution=5)), json.dumps(cfg(finish=[])),
            json.dumps(cfg(models__critic="prov/critic-1")),
            json.dumps(cfg(roles__workers=[{"a": 1}])),
            json.dumps(cfg(finish__allow_merge="false")),
            json.dumps(cfg(execution__max_fails=True)),
            json.dumps(cfg(finish__max_fix_rounds=0)),
        ]
        for text in cases:
            for args in (("validate",), ("cmd", "workers"), ("show",)):
                r = run_cli(text, *args)
                self.assertNotIn("Traceback", r.stderr, (text, args, r.stderr))
                if args[0] != "show":
                    self.assertEqual(r.returncode, 1, (text, args))
                    self.assertIn("kstack: invalid config", r.stderr, (text, args))


class WarningsTest(unittest.TestCase):
    def test_diverse_config_has_no_warnings(self):
        self.assertEqual(km.warnings(cfg()), [])

    def test_same_model_configs_allowed_with_warnings(self):
        c = cfg(roles__plan_critic="deep", roles__reviewer="builder", roles__verifiers=["critic", "critic"])
        self.assertEqual(km.problems(c), [])
        w = km.warnings(c)
        self.assertIn("planner and plan_critic use the same model; the cross-check loses diversity", w)
        self.assertIn("a reviewer or verifier shares a model with a worker; prefer a different one", w)
        self.assertIn("the two audit lanes run on one model; list two different verifiers first", w)
        r = run_cli(c, "validate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count("warning:"), 3)

    def test_single_verifier_warns(self):
        self.assertIn("the two audit lanes run on one model; list two different verifiers first",
                      km.warnings(cfg(roles__verifiers=["critic"])))

    def test_equivalent_ids_across_clis_warn_without_rewrite(self):
        c = cfg(models__critic={"cli": "pi", "model": "openai/GPT-Deep", "effort": "high"})
        self.assertIn("planner and plan_critic use the same model; the cross-check loses diversity",
                      km.warnings(c))
        self.assertEqual(c["models"]["critic"]["model"], "openai/GPT-Deep")
        self.assertEqual(km.argv(c["models"]["critic"]), ["pi", "--model", "openai/GPT-Deep:high"])


PI_LISTING = ("provider      model           context\n"
              "prov          critic-1        1M\n"
              "prov          builder-1       1M\n"
              "prov          builder-2       1M\n"
              "prov          checker-1       1M\n")


def completed(rc=0, out="", err=""):
    return subprocess.CompletedProcess(["pi", "--list-models"], rc, out, err)


class AvailabilityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.dict(os.environ, {"CODEX_HOME": str(Path(self.tmp.name) / "codex")})
        p.start()
        self.addCleanup(p.stop)
        w = mock.patch.object(km.shutil, "which", return_value="/fake/pi")
        w.start()
        self.addCleanup(w.stop)

    def pi_only(self):
        c = cfg()
        del c["models"]["deep"]
        return c

    def write_codex_catalog(self, catalog_text):
        home = Path(self.tmp.name) / "codex"
        home.mkdir(exist_ok=True)
        cat = Path(self.tmp.name) / "catalog.json"
        cat.write_text(catalog_text)
        (home / "config.toml").write_text('model_catalog_json = "%s"\n' % cat)

    def test_pi_listing_ok(self):
        with mock.patch.object(km.subprocess, "run", return_value=completed(out=PI_LISTING)) as run:
            bad, notes = km.availability(self.pi_only())
        self.assertEqual((bad, notes), ([], []))
        self.assertEqual(run.call_args[1]["timeout"], km.PI_LIST_TIMEOUT)
        self.assertEqual(run.call_args[1]["env"]["PI_OFFLINE"], "1")

    def test_known_invalid_pi_model_still_fails(self):
        c = self.pi_only()
        c["models"]["critic"]["model"] = "prov/ghost-9"
        with mock.patch.object(km.subprocess, "run", return_value=completed(out=PI_LISTING)):
            bad, notes = km.availability(c)
        self.assertEqual(bad, ["model critic: prov/ghost-9 not in `pi --list-models`"])
        self.assertEqual(notes, [])

    def assert_unavailable(self, side_effect=None, return_value=None, expect=""):
        with mock.patch.object(km.subprocess, "run", side_effect=side_effect, return_value=return_value):
            bad, notes = km.availability(self.pi_only())
        self.assertEqual(bad, [])
        self.assertEqual(len(notes), 1, notes)
        self.assertIn(expect, notes[0])
        self.assertIn("pi presets not checked", notes[0])

    def test_pi_nonzero_exit_is_unavailable_not_invalid(self):
        self.assert_unavailable(return_value=completed(rc=2, out="", err="boom\nauth missing"),
                                expect="exited 2: auth missing")

    def test_pi_timeout_is_unavailable_not_invalid(self):
        self.assert_unavailable(side_effect=subprocess.TimeoutExpired(["pi"], km.PI_LIST_TIMEOUT),
                                expect="timed out after %ss" % km.PI_LIST_TIMEOUT)

    def test_pi_oserror_is_unavailable_not_invalid(self):
        self.assert_unavailable(side_effect=PermissionError(13, "Permission denied"), expect="could not run")

    def test_pi_empty_listing_is_unavailable_not_invalid(self):
        self.assert_unavailable(return_value=completed(out="provider model context\n"), expect="listed no models")

    def test_pi_not_installed(self):
        with mock.patch.object(km.shutil, "which", return_value=None), \
                mock.patch.object(km.subprocess, "run") as run:
            bad, notes = km.availability(self.pi_only())
        run.assert_not_called()
        self.assertEqual(bad, [])
        self.assertEqual(notes, ["pi not installed; pi presets not checked"])

    def test_codex_catalog_missing_is_unavailable(self):
        with mock.patch.object(km.subprocess, "run", return_value=completed(out=PI_LISTING)):
            bad, notes = km.availability(cfg())
        self.assertEqual(bad, [])
        self.assertEqual(notes, ["no Codex model catalog found; codex presets not checked"])

    def test_codex_catalog_checks_kept(self):
        self.write_codex_catalog(json.dumps({"models": [
            {"slug": "gpt-deep", "supported_reasoning_levels": [{"effort": "low"}, {"effort": "high"}]}]}))
        with mock.patch.object(km.subprocess, "run", return_value=completed(out=PI_LISTING)):
            self.assertEqual(km.availability(cfg()), ([], []))
            bad, _ = km.availability(cfg(models__deep__effort="xhigh"))
            self.assertEqual(bad, ["model deep: effort xhigh not supported by gpt-deep"])
            bad, _ = km.availability(cfg(models__deep__model="gpt-ghost"))
            self.assertEqual(bad, ["model deep: gpt-ghost not in the Codex catalog"])

    def test_codex_catalog_unreadable_is_unavailable(self):
        for text in ("{not json", json.dumps({"models": [{"no_slug": 1}]}), "[]"):
            self.write_codex_catalog(text)
            with mock.patch.object(km.subprocess, "run", return_value=completed(out=PI_LISTING)):
                bad, notes = km.availability(cfg())
            self.assertEqual(bad, [], text)
            self.assertEqual(len(notes), 1, (text, notes))
            self.assertIn("Codex model catalog unreadable", notes[0])


class ValidateCheckCliTest(unittest.TestCase):
    """End-to-end validate --check with a fake `pi` on PATH (no real model calls)."""

    def fake_pi(self, d, body):
        path = Path(d) / "pi"
        path.write_text("#!/bin/sh\n" + body)
        path.chmod(0o755)
        return {"PATH": "%s%s%s" % (d, os.pathsep, os.environ.get("PATH", ""))}

    def test_failing_pi_warns_and_passes(self):
        with tempfile.TemporaryDirectory() as d:
            r = run_cli(cfg(), "validate", "--check", env_extra=self.fake_pi(d, "echo nope >&2\nexit 3\n"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("warning: `pi --list-models` exited 3: nope; pi presets not checked", r.stdout)
        self.assertNotIn("not in `pi --list-models`", r.stdout + r.stderr)

    def test_working_pi_rejects_unknown_model(self):
        c = cfg(models__critic__model="prov/ghost-9")
        listing = PI_LISTING.replace("\n", "\\n")
        with tempfile.TemporaryDirectory() as d:
            r = run_cli(c, "validate", "--check", env_extra=self.fake_pi(d, "printf '%s'\n" % listing))
        self.assertEqual(r.returncode, 1)
        self.assertIn("model critic: prov/ghost-9 not in `pi --list-models`", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
