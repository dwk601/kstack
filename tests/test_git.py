"""Offline script scenarios: isolated Git, file:// remotes and a fixture gh API."""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/kstack-finish/scripts/kstack-git"
_loader = importlib.machinery.SourceFileLoader("kstack_git", str(SCRIPT))
_spec = importlib.util.spec_from_loader("kstack_git", _loader)
kg = importlib.util.module_from_spec(_spec)
_loader.exec_module(kg)


@unittest.skipUnless(shutil.which("git"), "Git is required for local semantic sandboxes")
class GitScriptTests(unittest.TestCase):
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
        # Same isolation as the former GitCleanupSemanticsTests: no Git routing,
        # injected config, inherited identity or credentials; only file transport.
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"),
                        KSTACK_CONFIG=str(home / "missing.json"),
                        LC_ALL="C", LANG="C",
                        GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_SYSTEM=os.devnull,
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0",
                        GIT_ALLOW_PROTOCOL="file", GIT_AUTHOR_NAME="Sandbox",
                        GIT_AUTHOR_EMAIL="sandbox@example.invalid",
                        GIT_COMMITTER_NAME="Sandbox",
                        GIT_COMMITTER_EMAIL="sandbox@example.invalid")
        self.real_git = shutil.which("git")
        self.git("init", "--initial-branch=main")
        self.git("config", "core.hooksPath", str(self.hooks))
        self.commit("product.md", "Tracked product documentation\n")
        self.commit(".gitignore", "ignored/\n")
        self.base = self.tip()
        self.git("init", "--bare", "--initial-branch=main", str(self.remote))
        self.git("remote", "add", "origin", self.remote.as_uri())
        self.git("push", "origin", "main")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.env["PATH"] = str(self.bin) + os.pathsep + self.env["PATH"]

    def git(self, *args, cwd=None, check=True, env=None):
        return subprocess.run(
            [self.real_git, "-c", "core.hooksPath=" + str(self.hooks), *map(str, args)],
            cwd=cwd or self.repo, env=self.env if env is None else env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check, timeout=15)

    def commit(self, relative, content, cwd=None):
        path = (cwd or self.repo) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        self.git("add", "--", relative, cwd=cwd)
        self.git("commit", "-m", "sandbox change", cwd=cwd)
        return self.tip(cwd=cwd)

    def tip(self, ref="HEAD", cwd=None):
        return self.git("rev-parse", ref, cwd=cwd).stdout.strip()

    def cli(self, cmd, *args, outcome="done", contains=None):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), cmd, *map(str, args)],
                                cwd=self.repo, env=self.env, capture_output=True,
                                text=True, timeout=20)
        self.assertEqual(result.returncode, {"done": 0, "absent": 0, "retained": 3, "error": 2}[outcome],
                         result.stdout + result.stderr)
        self.last_stdout = result.stdout
        line = result.stdout.splitlines()[-1]
        self.assertTrue(line.startswith("kstack-git " + cmd + " " + outcome + " "), line)
        if contains:
            self.assertIn(contains, line)
        return line.split(" ", 3)[3]

    def local_delete(self, name="worker", expect=None, outcome="done", extra=(), contains=None):
        return self.cli("delete-local-branch", "--branch", name, "--expect", expect or self.base,
                        "--base", "origin/main", *extra, outcome=outcome, contains=contains)

    def config_digest(self, name="worker"):
        return self.cli("snapshot-branch-config", "--branch", name)

    def config_entries(self):
        return tuple(self.git("config", "--local", "--no-includes", "--null", "--list")
                     .stdout.rstrip("\0").split("\0"))

    def branch_config(self, name):
        return tuple(e for e in self.config_entries()
                     if e.partition("\n")[0].rpartition(".")[0] == "branch." + name)

    def assert_absent_ref(self, name="worker"):
        self.assertEqual(self.git("show-ref", "--verify", "--quiet", "refs/heads/" + name,
                                  check=False).returncode, 1)

    def detached(self, name="verifier"):
        path = self.root / name
        self.git("worktree", "add", "--detach", str(path), self.base)
        return path

    def scratch_digest(self, path):
        return self.cli("scratch-digest", "--path", path)

    def test_integrated_cleanup_and_idempotent_absence(self):
        self.git("switch", "-c", "worker")
        tip = self.commit("worker.txt", "reviewed worker result\n")
        self.git("switch", "-c", "delivery")
        delivery = self.commit("delivery.txt", "later integration\n")
        self.git("switch", "main")
        self.git("merge", "--ff-only", "delivery")
        self.git("push", "origin", "main", "worker", "delivery")
        verifier = self.detached()
        for outcome in ("done", "absent"):
            self.cli("remove-worktree", "--path", verifier, "--expect-head", self.base, outcome=outcome)
            self.cli("delete-remote-branch", "--remote", "origin", "--branch", "worker",
                     "--expect", tip, outcome=outcome)
            self.local_delete(expect=tip, outcome=outcome)
            self.assert_absent_ref()
            self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/worker").stdout, "")
            self.assertFalse(verifier.exists())
            self.assertNotIn(str(verifier), self.git("worktree", "list", "--porcelain").stdout)
        self.assertEqual(self.tip("main"), delivery)

    def test_stale_remote_lease_and_git_errors_never_absence(self):
        self.git("switch", "-c", "worker")
        self.git("push", "origin", "worker")
        advanced = self.commit("new.txt", "advanced\n")
        self.git("push", "origin", "worker")
        self.cli("delete-remote-branch", "--remote", "origin", "--branch", "worker",
                 "--expect", self.base, outcome="retained", contains="tip changed")
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/worker").stdout.split()[0], advanced)
        self.cli("delete-remote-branch", "--remote", "missing", "--branch", "worker",
                 "--expect", advanced, outcome="error")

    def git_wrapper(self, code):
        wrapper = self.bin / "git"
        wrapper.write_text("#!" + sys.executable + "\nimport os, sys, subprocess\n"
                           + "REAL = " + repr(self.real_git) + "\n" + code
                           + "\nos.execv(REAL, [REAL, *sys.argv[1:]])\n")
        wrapper.chmod(0o755)

    def test_remote_post_delete_read_error_is_not_absence(self):
        self.git("branch", "worker")
        self.git("push", "origin", "worker")
        self.git_wrapper("if sys.argv[1] == 'push':\n"
                         "    result = subprocess.run([REAL, *sys.argv[1:]])\n"
                         "    os.rename(" + repr(str(self.remote)) + ", "
                         + repr(str(self.root / "disconnected.git")) + ")\n"
                         "    sys.exit(result.returncode)\n")
        self.cli("delete-remote-branch", "--remote", "origin", "--branch", "worker",
                 "--expect", self.base, outcome="error")
        self.assertEqual(self.tip("worker"), self.base)

    def test_atomic_local_deletion_rejects_racing_tip(self):
        self.git("branch", "worker", self.base)
        advanced = self.commit("new.txt", "concurrent commit\n")
        self.git("push", "origin", "main")
        self.git("config", "branch.worker.note", "keep on failed CAS")
        digest = self.config_digest()
        self.git_wrapper("if sys.argv[1:4] == ['update-ref', '-d', 'refs/heads/worker']:\n"
                         "    subprocess.run([REAL, 'update-ref', 'refs/heads/worker', " + repr(advanced) + "], check=True)\n")
        self.local_delete(extra=("--config-digest", digest), outcome="retained", contains="CAS rejected")
        self.assertEqual(self.tip("worker"), advanced)
        self.assertTrue(self.branch_config("worker"))

    def test_remote_race_at_push_is_leased_not_retried(self):
        self.git("branch", "worker", self.base)
        self.git("push", "origin", "worker")
        advanced = self.commit("advance", "race\n")
        self.git("push", "origin", "main")  # object must exist on remote
        self.git_wrapper("if sys.argv[1] == 'push':\n"
                         "    assert sys.argv[2] == " + repr("--force-with-lease=refs/heads/worker:" + self.base) + "\n"
                         "    subprocess.run([REAL, '--git-dir', " + repr(str(self.remote))
                         + ", 'update-ref', 'refs/heads/worker', " + repr(advanced) + "], check=True)\n")
        self.cli("delete-remote-branch", "--remote", "origin", "--branch", "worker",
                 "--expect", self.base, outcome="retained")
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "refs/heads/worker").stdout.split()[0], advanced)

    def test_dirty_and_ignored_worktree_retained(self):
        for ignored in (False, True):
            path = self.detached("ignored" if ignored else "dirty")
            file = path / ("ignored/unknown.md" if ignored else "product.md")
            file.parent.mkdir(exist_ok=True)
            file.write_text("unrecorded content\n")
            self.cli("remove-worktree", "--path", path, outcome="retained", contains="content")
            self.assertTrue(file.exists())
            self.assertIn(str(path), self.git("worktree", "list", "--porcelain").stdout)

    def test_locked_worktree_and_branch_association(self):
        path = self.root / "locked"
        self.git("worktree", "add", "-b", "worker", str(path), self.base)
        self.git("worktree", "lock", "--reason", "active", str(path))
        self.cli("remove-worktree", "--path", path, outcome="retained", contains="locked")
        self.local_delete(outcome="retained", contains="associated")
        self.assertEqual(self.tip("worker"), self.base)
        self.cli("remove-worktree", "--path", self.repo, outcome="retained", contains="main")

    def test_paused_interactive_rebase_in_other_worktree(self):
        path = self.root / "rebasing"
        self.git("worktree", "add", "-b", "worker", str(path), self.base)
        tip = self.commit("worker.txt", "reviewed change\n", cwd=path)
        # Integrate tip so the marker, not the ancestry gate, prevents deletion.
        self.git("merge", "--ff-only", "worker")
        self.git("push", "origin", "main")
        editor = shlex.join([sys.executable, "-c", "import pathlib,sys; p=pathlib.Path(sys.argv[1]); "
                             "p.write_text(p.read_text().replace('pick ', 'edit ', 1))"])
        self.git("rebase", "-i", self.base, cwd=path, env={**self.env, "GIT_SEQUENCE_EDITOR": editor})
        self.assertEqual(self.git("symbolic-ref", "--quiet", "HEAD", cwd=path, check=False).returncode, 1)
        self.assertEqual(self.git("status", "--porcelain", cwd=path).stdout, "")
        self.local_delete(expect=tip, outcome="retained", contains="operation marker")
        self.cli("remove-worktree", "--path", path, outcome="retained", contains="operation marker")
        self.assertEqual(self.tip("worker"), tip)
        self.git("rebase", "--abort", cwd=path)

    def test_main_worktree_markers_and_symlink_markers(self):
        self.git("branch", "worker")
        for marker in kg.MARKERS:
            file = self.repo / ".git" / marker
            file.symlink_to(self.root / "nonexistent")
            self.local_delete(outcome="retained", contains="operation marker")
            self.assertEqual(self.tip("worker"), self.base)
            file.unlink()

    def test_config_exact_section_duplicates_multiline_prefix_siblings(self):
        self.git("branch", "worker")
        self.git("push", "-u", "origin", "worker")
        for value in ("first\nline", "second"):
            self.git("config", "--add", "branch.worker.note", value)
            self.git("config", "--add", "branch.worker.extra.note", value)
        self.git("config", "branch.other.remote", "unrelated")
        snapshot = self.branch_config("worker")
        unrelated = tuple(e for e in self.config_entries() if e not in snapshot)
        digest = self.config_digest()
        self.assertEqual(digest, self.config_digest())
        self.assertNotEqual(digest, self.config_digest("absent-section"))
        self.assertRegex(digest, r"^[a-f0-9]{64}$")
        self.local_delete(extra=("--config-digest", digest))
        self.assert_absent_ref()
        self.assertEqual(self.branch_config("worker"), ())
        self.assertEqual(self.config_entries(), unrelated)
        self.assertEqual(len(self.branch_config("worker.extra")), 2)

    def test_changed_missing_and_nonlocal_config_proofs_retained(self):
        for case in ("changed", "missing", "global"):
            name = "worker-" + case
            self.git("branch", name)
            self.git("config", "branch." + name + ".note", "owned")
            digest = self.config_digest(name)
            extra = ("--config-digest", digest)
            if case == "changed":
                self.git("config", "branch." + name + ".note", "another writer")
            elif case == "missing":
                extra = ()
            else:
                global_file = self.root / "global-config"
                global_file.write_text('[branch "' + name + '"]\n note = global\n')
                self.env["GIT_CONFIG_GLOBAL"] = str(global_file)
                extra = ("--config-digest", self.config_digest(name))
            self.local_delete(name=name, extra=extra, outcome="retained", contains="local-ref deleted")
            self.assert_absent_ref(name)
            self.assertTrue(self.branch_config(name))
            self.local_delete(name=name, extra=extra, outcome="absent", contains="config untouched")
            self.assertTrue(self.branch_config(name))

    def test_absent_config_idempotent(self):
        self.git("branch", "worker")
        before = self.config_entries()
        absence = self.config_digest()
        self.local_delete(contains="config absent")
        self.local_delete(outcome="absent")
        self.assertEqual(self.config_digest(), absence)
        self.assertEqual(self.config_entries(), before)

    def prepare_sync(self, conflict=False):
        self.git("switch", "-c", "owned-local")
        original = self.commit("product.md" if conflict else "local.txt", "owned local edit\n")
        self.git("switch", "-c", "delivered", self.base)
        delivered = self.commit("product.md" if conflict else "delivered.txt", "remote work\n")
        self.git("push", "origin", "HEAD:main")
        return original, delivered

    def test_sync_ff_and_owned_rebase(self):
        original, delivered = self.prepare_sync()
        self.git("switch", "main")
        self.cli("sync-local", "--base", "main")
        self.assertEqual(self.tip(), delivered)
        # Restore the old base to exercise the not-checked-out CAS path as well.
        self.git("switch", "owned-local")
        self.git("update-ref", "refs/heads/main", self.base, delivered)
        self.cli("sync-local", "--base", "main", "--owned-branch", "owned-local", "--owned-expect", original)
        self.assertEqual(self.tip("main"), delivered)
        self.assertNotEqual(self.tip(), original)
        self.git("merge-base", "--is-ancestor", delivered, "HEAD")
        self.assertEqual((self.repo / "local.txt").read_text(), "owned local edit\n")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_sync_conflict_preserves_commits(self):
        original, delivered = self.prepare_sync(conflict=True)
        self.git("switch", "owned-local")
        self.cli("sync-local", "--base", "main", "--owned-branch", "owned-local",
                 "--owned-expect", original, outcome="retained", contains="commits preserved")
        self.assertEqual(self.tip(), original)
        self.assertEqual(self.tip("main"), delivered)
        self.assertEqual((self.repo / "product.md").read_text(), "owned local edit\n")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        self.assertFalse((self.repo / ".git/rebase-merge").exists())

    def test_sync_dirty_divergent_unowned_and_stale_owned_retained(self):
        original, delivered = self.prepare_sync()
        self.cli("sync-local", "--base", "main", outcome="retained", contains="unowned")
        self.git("switch", "owned-local")
        self.cli("sync-local", "--base", "main", "--owned-branch", "owned-local",
                 "--owned-expect", self.base, outcome="retained", contains="tip changed")
        (self.repo / "dirty").write_text("unknown")
        self.cli("sync-local", "--base", "main", "--owned-branch", "owned-local",
                 "--owned-expect", original, outcome="retained", contains="dirty")
        (self.repo / "dirty").unlink()
        self.git("switch", "main")
        divergence = self.commit("divergence", "do not discard")
        self.cli("sync-local", "--base", "main", outcome="retained", contains="divergent")
        self.assertEqual(self.tip(), divergence)
        self.assertEqual(self.tip("owned-local"), original)
        self.assertEqual(self.tip("origin/main"), delivered)

    def test_sync_base_associated_elsewhere_and_operation_markers(self):
        self.git("worktree", "add", "-b", "owned-local", str(self.root / "other"), self.base)
        self.git("switch", "--detach")
        self.git("worktree", "add", str(self.root / "base-checkout"), "main")
        self.git("worktree", "remove", str(self.root / "other"))
        self.git("switch", "owned-local")
        self.cli("sync-local", "--base", "main", "--owned-branch", "owned-local",
                 "--owned-expect", self.base, outcome="retained", contains="base checked out")
        marker = self.repo / ".git/REVERT_HEAD"
        marker.write_text(self.base)
        self.cli("sync-local", "--base", "main", "--owned-branch", "owned-local",
                 "--owned-expect", self.base, outcome="retained", contains="operation marker")
        self.assertEqual(self.tip(), self.base)
        self.assertIn('"upstream":', self.last_stdout)
        self.assertIn('"status":', self.last_stdout)

    def test_symbolic_local_branch_cannot_delete_its_target(self):
        self.git("symbolic-ref", "refs/heads/worker", "refs/heads/main")
        self.local_delete(outcome="retained", contains="symbolic ref")
        self.assertEqual(self.tip("main"), self.base)
        self.assertEqual(self.tip("worker"), self.base)

    def test_unique_unmerged_commit_retained(self):
        self.git("switch", "-c", "worker")
        tip = self.commit("unique.txt", "not delivered\n")
        self.git("switch", "main")
        self.local_delete(expect=tip, outcome="retained", contains="unmerged")
        self.assertEqual(self.tip("worker"), tip)

    def test_scratch_untracked_literal_vs_tracked(self):
        artifact = self.repo / "owned[1]*.md"
        artifact.write_text("ephemeral\n")
        self.cli("delete-scratch", "--path", artifact, "--expect", self.scratch_digest(artifact), "--root", self.repo)
        self.assertFalse(artifact.exists())
        product = self.repo / "product.md"
        self.cli("delete-scratch", "--path", product, "--expect", self.scratch_digest(product),
                 "--root", self.repo, outcome="retained", contains="tracked")
        self.assertTrue(product.exists())

    def test_scratch_directory_tracked_member_and_git_errors(self):
        directory = self.repo / "owned"
        directory.mkdir()
        (directory / "ephemeral").write_text("temporary")
        self.commit("owned/product", "tracked product")
        digest = self.scratch_digest(directory)
        self.cli("delete-scratch", "--path", directory, "--expect", digest, "--root", self.repo,
                 outcome="retained", contains="tracked")
        self.assertTrue((directory / "ephemeral").exists())
        artifact = self.repo / "temp"
        artifact.write_text("temporary")
        digest = self.scratch_digest(artifact)
        self.env["GIT_DIR"] = str(self.root / "invalid-git-dir")
        self.cli("delete-scratch", "--path", artifact, "--expect", digest, "--root", self.repo,
                 outcome="error", contains="cannot inspect")
        self.assertTrue(artifact.exists())

    def test_scratch_symlinks_escape_hash_and_entry_changes(self):
        owned = self.root / "owned"
        owned.mkdir()
        scratch = owned / "scratch"
        scratch.mkdir()
        file = scratch / "fixture"
        file.write_text("original")
        digest = self.scratch_digest(scratch)
        file.write_text("changed")
        self.cli("delete-scratch", "--path", scratch, "--root", owned, "--expect", digest,
                 outcome="retained", contains="changed")
        file.write_text("original")
        (scratch / "extra").write_text("extra")
        self.cli("delete-scratch", "--path", scratch, "--root", owned, "--expect", digest,
                 outcome="retained", contains="changed")
        (scratch / "extra").unlink()
        link = owned / "link"
        link.symlink_to(scratch, target_is_directory=True)
        for path in (link, link / "fixture", scratch / "../link/fixture", link / "../scratch"):
            self.cli("delete-scratch", "--path", path, "--root", owned, "--expect", digest,
                     outcome="retained", contains="symlink")
            self.cli("scratch-digest", "--path", path, outcome="retained", contains="symlink")
        (scratch / "sym").symlink_to(file)
        self.cli("scratch-digest", "--path", scratch, outcome="retained", contains="symlink")
        (scratch / "sym").unlink()
        for path in (owned, self.repo / "product.md", owned / "../repo/product.md"):
            self.cli("delete-scratch", "--path", path, "--root", owned, "--expect", digest,
                     outcome="retained", contains="contained")
        self.cli("delete-scratch", "--path", scratch, "--root", owned, "--expect", digest)
        self.cli("delete-scratch", "--path", scratch, "--root", owned, "--expect", digest, outcome="absent")
        self.assertFalse(scratch.exists())
        self.assertTrue((self.repo / "product.md").exists())

    def test_scratch_recheck_after_git_inspection(self):
        artifact = self.repo / "owned-temp"
        artifact.write_text("before")
        digest = self.scratch_digest(artifact)
        self.git_wrapper("if 'ls-files' in sys.argv:\n"
                         "    open(" + repr(str(artifact)) + ", 'w').write('raced')\n")
        self.cli("delete-scratch", "--path", artifact, "--expect", digest, "--root", self.repo,
                 outcome="retained", contains="changed before unlink")
        self.assertEqual(artifact.read_text(), "raced")

    def test_missing_worktree_metadata_is_retained(self):
        path = self.detached("missing")
        shutil.rmtree(path)
        self.cli("remove-worktree", "--path", path, outcome="retained", contains="metadata")
        self.assertIn(str(path), self.git("worktree", "list", "--porcelain").stdout)
        self.assertFalse(path.exists())

    def test_unregistered_or_changed_head_worktree_retained(self):
        path = self.detached()
        wrong = self.commit("new", "new commit")
        self.cli("remove-worktree", "--path", path, "--expect-head", wrong, outcome="retained", contains="HEAD changed")
        self.cli("remove-worktree", "--path", self.root, outcome="retained", contains="not a registered")
        self.assertTrue(path.exists())

    def fake_gh(self, head=None, merge=None, polls=1, initial="OPEN"):
        self.gh_state = self.root / "gh-state.json"
        self.gh_state.write_text(json.dumps(dict(head=head or self.base, merge=merge or self.base,
                                                 polls=polls, state=initial, calls=[], requested=False)))
        self.env["FAKE_GH_STATE"] = str(self.gh_state)
        executable = self.bin / "gh"
        executable.write_text("#!" + sys.executable + "\n" + '''import json, os, pathlib, sys
p = pathlib.Path(os.environ['FAKE_GH_STATE'])
s = json.loads(p.read_text())
s['calls'].append(sys.argv[1:])
if sys.argv[1:3] == ['pr', 'merge']:
    assert '--delete-branch' not in sys.argv
    assert sys.argv[-2:] == ['--match-head-commit', s['head']]
    s['requested'] = True
else:
    if s['requested']:
        s['polls'] -= 1
        if s['polls'] <= 0:
            s['state'] = 'MERGED'
    print(json.dumps(dict(state=s['state'], headRefOid=s['head'],
                         mergeCommit={'oid': s['merge']}, baseRefName='main')))
p.write_text(json.dumps(s))
''')
        executable.chmod(0o755)

    def merge_cli(self, *extra, outcome="done", contains=None, head=None, method="merge"):
        return self.cli("merge-pr", "--pr", "7", "--match-head", head or self.base,
                        "--method", method, "--timeout-seconds", "2", *extra,
                        outcome=outcome, contains=contains)

    def test_merge_permission_refused_even_with_repo_config(self):
        self.fake_gh()
        (self.repo / "config.json").write_text('{"finish":{"allow_merge":true}}')
        self.git("config", "finish.allow-merge", "true")
        self.merge_cli(outcome="error", contains="permission")
        self.assertEqual(json.loads(self.gh_state.read_text())["calls"], [])
        Path(self.env["KSTACK_CONFIG"]).write_text('{"finish":{"allow_merge":1}}')
        self.merge_cli(outcome="error", contains="permission")
        self.assertEqual(json.loads(self.gh_state.read_text())["calls"], [])

    def test_merge_user_consent_polling_and_no_delete_branch(self):
        self.fake_gh(polls=3)
        self.merge_cli("--user-consented", contains=self.base)
        state = json.loads(self.gh_state.read_text())
        self.assertEqual(state["state"], "MERGED")
        merges = [c for c in state["calls"] if c[:2] == ["pr", "merge"]]
        self.assertEqual(merges, [["pr", "merge", "7", "--merge", "--match-head-commit", self.base]])
        self.assertGreaterEqual(len(state["calls"]), 5)
        self.assertEqual(self.tip("origin/main"), self.base)

    def test_merge_user_config_resolution_and_boolean_true(self):
        for location in ("override", "xdg", "home"):
            with self.subTest(location=location):
                self.fake_gh()
                if location == "override":
                    path = Path(self.env["KSTACK_CONFIG"])
                else:
                    self.env.pop("KSTACK_CONFIG", None)
                    if location == "home":
                        self.env.pop("XDG_CONFIG_HOME", None)
                    path = Path(self.env.get("XDG_CONFIG_HOME", str(Path(self.env["HOME"]) / ".config"))) / "kstack/config.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{"finish":{"allow_merge":true}}')
                self.merge_cli()

    def test_merge_head_mismatch_refused(self):
        other = self.commit("head", "different head")
        self.fake_gh(head=other)
        self.merge_cli("--user-consented", outcome="error", contains="matched head")
        self.assertFalse(json.loads(self.gh_state.read_text())["requested"])

    def test_merge_timeout_and_ancestry_failure(self):
        self.fake_gh(polls=100)
        self.merge_cli("--user-consented", "--timeout-seconds", "0.2", outcome="error", contains="timeout")
        unmerged = self.commit("unmerged", "not on remote")
        self.fake_gh(merge=unmerged)
        self.merge_cli("--user-consented", outcome="error", contains="merge SHA not on fetched base")
        self.fake_gh(head=unmerged)
        self.merge_cli("--user-consented", head=unmerged, outcome="error", contains="verified head not on fetched base")

    def test_squash_mapping_allows_local_deletion_and_merge(self):
        self.git("switch", "-c", "worker")
        tip = self.commit("worker", "worker unique commit")
        self.git("switch", "main")
        self.git("merge", "--squash", "worker")
        self.git("commit", "-m", "squashed")
        merge = self.tip()
        self.git("push", "origin", "main")
        self.fake_gh(head=tip, merge=merge)
        self.merge_cli("--user-consented", head=tip, method="squash", contains=merge)
        self.fake_gh(head=tip, merge=merge, initial="MERGED")
        self.local_delete(expect=tip, extra=("--pr", "7"))
        self.assert_absent_ref()


class ScriptInterfaceTests(unittest.TestCase):
    def test_help_has_final_done_line(self):
        for args in (["--help"], ["delete-local-branch", "--help"]):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = kg.main(args)
            self.assertEqual(code, 0)
            self.assertTrue(out.getvalue().splitlines()[-1].endswith(" done help"))

    def test_bad_arguments_have_final_error_line(self):
        for args in ([], ["nonsense"], ["merge-pr"], ["merge-pr", "--pr", "0"]):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = kg.main(args)
            self.assertEqual(code, 2)
            self.assertRegex(out.getvalue().splitlines()[-1], r"^kstack-git \S+ error .+")

    def test_git_errors_do_not_prove_absence(self):
        with mock.patch.object(kg, "git", side_effect=kg.Failure("Git path error")):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = kg.main(["delete-local-branch", "--branch", "worker", "--expect", "a" * 40,
                                "--base", "origin/main"])
        self.assertEqual(code, 2)
        self.assertIn("error Git path error", out.getvalue())


if __name__ == "__main__":
    unittest.main()
