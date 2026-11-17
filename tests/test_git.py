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

try:
    import resource
except ImportError:
    resource = None

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
        self.raw_root = Path(self.temp.name)
        self.root = self.raw_root.resolve()
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

    def cli(self, cmd, *args, outcome="done", contains=None, cwd=None, fd_limit=None):
        def limit_descriptors():
            _, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            limit = fd_limit if hard == resource.RLIM_INFINITY else min(fd_limit, hard)
            resource.setrlimit(resource.RLIMIT_NOFILE, (limit, hard))

        result = subprocess.run([sys.executable, "-B", str(SCRIPT), cmd, *map(str, args)],
                                cwd=cwd or self.repo, env=self.env, capture_output=True,
                                text=True, timeout=90 if fd_limit else 20,
                                preexec_fn=limit_descriptors if fd_limit else None)
        self.assertEqual(result.returncode, {"done": 0, "absent": 0, "retained": 3, "error": 2}[outcome],
                         result.stdout + result.stderr)
        self.last_stdout = result.stdout
        line = result.stdout.splitlines()[-1]
        self.assertTrue(line.startswith("kstack-git " + cmd + " " + outcome + " "), line)
        if contains:
            self.assertIn(contains, line)
        return line.split(" ", 3)[3]

    @contextlib.contextmanager
    def sandbox(self, cwd=None):
        previous = Path.cwd()
        with mock.patch.dict(os.environ, self.env, clear=True):
            os.chdir(cwd or self.repo)
            try:
                yield
            finally:
                os.chdir(previous)

    def in_process(self, *args, outcome="done", contains=None):
        with self.sandbox(), contextlib.redirect_stdout(io.StringIO()) as out:
            result = kg.main(list(map(str, args)))
        self.assertEqual(result, {"done": 0, "absent": 0, "retained": 3, "error": 2}[outcome], out.getvalue())
        line = out.getvalue().splitlines()[-1]
        self.assertTrue(line.startswith("kstack-git " + args[0] + " " + outcome + " "), line)
        if contains:
            self.assertIn(contains, line)
        return out.getvalue()

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
        self.assertEqual(self.cli("remove-worktree", "--path", path, outcome="retained"), "locked worktree")
        self.local_delete(outcome="retained", contains="associated")
        self.assertEqual(self.tip("worker"), self.base)
        self.assertEqual(self.cli("remove-worktree", "--path", self.repo, outcome="retained"), "main worktree")

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
        # Deliberately independent of the implementation: deleting ANY marker
        # from kg.MARKERS must remove a real protection and fail this test.
        for marker in ("rebase-merge", "rebase-apply", "BISECT_START", "MERGE_HEAD",
                       "CHERRY_PICK_HEAD", "REVERT_HEAD", "sequencer"):
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

    def test_included_only_and_multi_file_branch_config_retained(self):
        for local_too in (False, True):
            name = "worker-multiple" if local_too else "worker-included"
            self.git("branch", name)
            if local_too:
                self.git("config", "branch." + name + ".note", "local entry")
            included = self.root / (name + ".config")
            content = '[branch "' + name + '"]\n note = included entry\n'
            included.write_text(content)
            self.git("config", "--add", "include.path", str(included))
            digest = self.config_digest(name)
            self.assertNotEqual(digest, self.config_digest("absent-section"))
            local_before = self.branch_config(name)
            self.local_delete(name=name, extra=("--config-digest", digest), outcome="retained",
                              contains="not in one local file" if local_too else "included config")
            self.assert_absent_ref(name)
            self.assertEqual(included.read_text(), content)
            self.assertEqual(self.branch_config(name), local_before)
            self.assertIn("included entry", self.git("config", "--includes", "--get-all",
                                                    "branch." + name + ".note").stdout.splitlines())

    def test_global_only_branch_config_cannot_be_removed(self):
        self.git("branch", "worker")
        config = self.root / "global-only.config"
        original = '[branch "worker"]\n note = user owned\n'
        config.write_text(original)
        self.env["GIT_CONFIG_GLOBAL"] = str(config)
        self.assertEqual(self.branch_config("worker"), ())
        digest = self.config_digest()
        self.local_delete(extra=("--config-digest", digest), outcome="retained",
                          contains="not in one local file")
        self.assert_absent_ref()
        self.assertEqual(config.read_text(), original)

    def test_config_digest_covers_scope_origin_and_file(self):
        first, second = self.root / "first.config", self.root / "second.config"
        for config in (first, second):
            config.write_text('[branch "worker"]\n note = same value\n')
        self.env["GIT_CONFIG_GLOBAL"] = str(first)
        global_first = self.config_digest()
        self.env["GIT_CONFIG_GLOBAL"] = str(second)
        global_second = self.config_digest()
        self.assertNotEqual(global_first, global_second, "origin/file must enter digest")
        self.env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=str(first), GIT_CONFIG_NOSYSTEM="0")
        system_first = self.config_digest()
        self.assertNotEqual(global_first, system_first, "scope must enter digest even for the SAME file")

    def test_config_snapshot_and_deletion_from_deep_subdirectory(self):
        self.git("branch", "worker")
        self.git("config", "branch.worker.note", "owned")
        digest = self.config_digest()
        sub = self.repo / "sub/deep"
        sub.mkdir(parents=True)
        self.assertEqual(self.cli("snapshot-branch-config", "--branch", "worker", cwd=sub), digest)
        self.cli("delete-local-branch", "--branch", "worker", "--expect", self.base,
                 "--base", "origin/main", "--config-digest", digest, cwd=sub)
        self.assert_absent_ref()
        self.assertEqual(self.branch_config("worker"), ())

    def test_config_snapshot_in_bare_repo_and_its_linked_worktree(self):
        absent = self.cli("snapshot-branch-config", "--branch", "worker", cwd=self.remote)
        for value in ("first\nline", "second"):
            self.git("config", "--add", "branch.worker.note", value, cwd=self.remote)
        self.git("config", "branch.worker.extra.note", "prefix sibling", cwd=self.remote)
        before = (self.remote / "config").read_bytes()
        digest = self.cli("snapshot-branch-config", "--branch", "worker", cwd=self.remote)
        self.assertRegex(digest, r"^[a-f0-9]{64}$")
        self.assertNotEqual(digest, absent)
        self.assertEqual(self.cli("snapshot-branch-config", "--branch", "worker",
                                  cwd=self.remote / "objects"), digest)
        linked = self.root / "bare-linked"
        self.git("worktree", "add", "--detach", str(linked), self.base, cwd=self.remote)
        self.assertEqual(self.cli("snapshot-branch-config", "--branch", "worker", cwd=linked), digest)
        self.assertEqual((self.remote / "config").read_bytes(), before)

    def test_post_cas_ref_readback_precedes_config_deletion(self):
        self.git("branch", "worker")
        self.git("config", "branch.worker.note", "retain until absence proven")
        digest = self.config_digest()
        before = self.branch_config("worker")
        self.git_wrapper("if sys.argv[1:3] == ['update-ref', '-d']:\n    sys.exit(0)\n")
        self.local_delete(extra=("--config-digest", digest), outcome="retained", contains="ref remains")
        self.assertEqual(self.tip("worker"), self.base)
        self.assertEqual(self.branch_config("worker"), before)

    def test_post_config_deletion_section_readback(self):
        self.git("branch", "worker")
        self.git("config", "branch.worker.note", "still here")
        digest = self.config_digest()
        before = self.branch_config("worker")
        self.git_wrapper("if '--remove-section' in sys.argv:\n    sys.exit(0)\n")
        self.local_delete(extra=("--config-digest", digest), outcome="retained", contains="section remains")
        self.assert_absent_ref()
        self.assertEqual(self.branch_config("worker"), before)

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

    def test_detached_checkout_cannot_be_owned_by_empty_branch(self):
        original, delivered = self.prepare_sync()
        self.git("switch", "--detach", original)
        for options in (("--owned-branch", "", "--owned-expect", original),
                        ("--owned-branch", "owned-local", "--owned-expect", original),
                        ("--owned-branch", "", "--owned-expect", "")):
            self.cli("sync-local", "--base", "main", *options,
                     outcome="retained", contains="unowned or detached")
            self.assertEqual(self.tip(), original)
            self.assertEqual(self.tip("main"), self.base)
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

    def test_literal_pathspec_magic_filename_is_untracked(self):
        artifact = self.repo / ":(top)product.md"
        artifact.write_text("ephemeral, not the tracked product.md")
        digest = self.scratch_digest(artifact)
        self.cli("delete-scratch", "--path", artifact, "--root", self.repo, "--expect", digest)
        self.assertFalse(artifact.exists())
        self.assertTrue((self.repo / "product.md").exists())

    def test_empty_tracked_gitlink_directory_is_not_scratch(self):
        sub = self.repo / "submodule"
        sub.mkdir()
        self.git("update-index", "--add", "--cacheinfo", "160000," + self.base + ",submodule")
        self.git("commit", "-m", "fixture gitlink")
        before = self.git("status", "--porcelain").stdout
        self.cli("delete-scratch", "--path", sub, "--root", self.repo,
                 "--expect", self.scratch_digest(sub), outcome="retained", contains="tracked")
        self.assertTrue(sub.is_dir())
        self.assertEqual(self.git("status", "--porcelain").stdout, before)

    def test_corrupt_index_cannot_authorize_tracked_scratch_deletion(self):
        product = self.repo / "product.md"
        before = product.read_bytes()
        digest = self.scratch_digest(product)
        (self.repo / ".git/index").write_bytes(b"corrupt index")
        self.cli("delete-scratch", "--path", product, "--root", self.repo, "--expect", digest,
                 outcome="error", contains="cannot prove untracked")
        self.assertEqual(product.read_bytes(), before)
        with self.sandbox(), self.assertRaisesRegex(kg.Failure, "git:"):
            kg.clean()

    def test_corrupt_head_is_not_outside_a_repository(self):
        product = self.repo / "product.md"
        before = product.read_bytes()
        digest = self.scratch_digest(product)
        (self.repo / ".git/HEAD").write_text("garbage HEAD\n")
        self.cli("delete-scratch", "--path", product, "--root", self.repo, "--expect", digest,
                 outcome="error", contains="cannot inspect scratch repository")
        self.assertEqual(product.read_bytes(), before)
        with self.sandbox(), self.assertRaisesRegex(kg.Failure, "git:"):
            kg.worktrees()
        with self.sandbox(), self.assertRaisesRegex(kg.Failure, "git:"):
            kg.ref_tip("refs/heads/main")

    def test_corrupt_ref_warning_is_not_absence(self):
        self.git("branch", "worker")
        (self.repo / ".git/refs/heads/worker").write_text("not an object id\n")
        self.local_delete(outcome="error", contains="uninspectable refs")
        self.assertTrue((self.repo / ".git/refs/heads/worker").exists())

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
        for path, expected in ((link, digest), (link / "fixture", self.scratch_digest(file))):
            self.cli("delete-scratch", "--path", path, "--root", owned, "--expect", expected,
                     outcome="retained", contains="symlink")
        for path in (scratch / "../link/fixture", link / "../scratch"):
            self.cli("delete-scratch", "--path", path, "--root", owned, "--expect", digest,
                     outcome="retained", contains="ancestor escape")
        self.cli("scratch-digest", "--path", link, outcome="retained", contains="symlink")
        # Digest has no owned-root argument: canonical ancestor aliases are OK,
        # but deletion above never follows a symlink beneath its owned root.
        self.assertEqual(self.scratch_digest(link / "fixture"), self.scratch_digest(file))
        (scratch / "sym").symlink_to(file)
        self.cli("scratch-digest", "--path", scratch, outcome="retained", contains="symlink")
        (scratch / "sym").unlink()
        for path in (owned, self.repo / "product.md", owned / "../repo/product.md"):
            self.cli("delete-scratch", "--path", path, "--root", owned, "--expect", digest,
                     outcome="retained")
        self.cli("delete-scratch", "--path", scratch, "--root", owned, "--expect", digest)
        self.cli("delete-scratch", "--path", scratch, "--root", owned, "--expect", digest, outcome="absent")
        self.assertFalse(scratch.exists())
        self.assertTrue((self.repo / "product.md").exists())

    def test_symlink_owned_root_leaf_is_not_followed(self):
        victim = self.root / "victim"
        file = victim / "dir/fixture"
        file.parent.mkdir(parents=True)
        file.write_text("unrelated user data")
        link = self.root / "rootlink"
        link.symlink_to(victim, target_is_directory=True)
        digest = self.scratch_digest(file)
        for root in (str(link), str(link) + "/"):
            self.cli("delete-scratch", "--path", link / "dir/fixture", "--root", root,
                     "--expect", digest, outcome="retained", contains="symlink owned root")
            self.assertEqual(file.read_text(), "unrelated user data")
        link.unlink()
        link.symlink_to(self.root / "missing", target_is_directory=True)
        self.cli("delete-scratch", "--path", link / "dir/fixture", "--root", link,
                 "--expect", digest, outcome="retained", contains="symlink owned root")

    def test_directory_nofollow_blocks_escape_with_the_file_own_digest(self):
        owned = self.root / "owned"
        owned.mkdir()
        victim = self.root / "victim"
        victim.mkdir()
        file = victim / "fixture"
        file.write_text("unrelated user data")
        (owned / "link").symlink_to(victim, target_is_directory=True)
        self.cli("delete-scratch", "--path", owned / "link/fixture", "--root", owned,
                 "--expect", self.scratch_digest(file), outcome="retained",
                 contains="symlink or changed directory component")
        self.assertEqual(file.read_text(), "unrelated user data")

    def test_git_routing_and_error_message_guards_outside_any_repo(self):
        owned = self.root / "owned"
        owned.mkdir()
        file = owned / "fixture"
        file.write_text("owned, but Git errors do not authorize deletion")
        digest = self.scratch_digest(file)
        for key, value in (("GIT_DIR", str(self.root / "missing.git")),
                           ("GIT_DIR", ""),
                           ("GIT_WORK_TREE", str(self.root / "missing-worktree"))):
            with self.subTest(key=key, value=value):
                self.env.pop("GIT_DIR", None)
                self.env.pop("GIT_WORK_TREE", None)
                self.env[key] = value
                self.cli("delete-scratch", "--path", file, "--root", owned, "--expect", digest,
                         outcome="error", contains="cannot inspect scratch repository")
                self.assertTrue(file.is_file())

    def test_scratch_recheck_after_git_inspection(self):
        artifact = self.repo / "owned-temp"
        artifact.write_text("before")
        digest = self.scratch_digest(artifact)
        self.git_wrapper("if 'ls-files' in sys.argv:\n"
                         "    open(" + repr(str(artifact)) + ", 'w').write('raced')\n")
        self.cli("delete-scratch", "--path", artifact, "--expect", digest, "--root", self.repo,
                 outcome="retained", contains="changed before unlink")
        self.assertEqual(artifact.read_text(), "raced")

    def test_scratch_ancestor_swap_after_last_snapshot_cannot_escape(self):
        owned = self.root / "owned"
        scratch = owned / "scratch"
        scratch.mkdir(parents=True)
        (scratch / "fixture").write_text("owned")
        victim = self.root / "victim"
        victim.mkdir()
        (victim / "fixture").write_text("unrelated user data")
        digest = self.scratch_digest(scratch)
        snapshot = kg.scratch_snapshot
        calls = []

        def swapped(*args, **kwargs):
            result = snapshot(*args, **kwargs)
            calls.append(1)
            if len(calls) == 2:
                scratch.rename(owned / "moved")
                scratch.symlink_to(victim, target_is_directory=True)
            return result

        with mock.patch.object(kg, "scratch_snapshot", side_effect=swapped):
            self.in_process("delete-scratch", "--path", scratch, "--root", owned,
                            "--expect", digest, outcome="retained", contains="changed before unlink")
        self.assertEqual((victim / "fixture").read_text(), "unrelated user data")
        self.assertEqual((owned / "moved/fixture").read_text(), "owned")

    def test_scratch_swap_during_unlink_uses_pinned_directory_fd(self):
        owned = self.root / "owned"
        scratch = owned / "scratch"
        scratch.mkdir(parents=True)
        (scratch / "fixture").write_text("owned")
        victim = self.root / "victim"
        victim.mkdir()
        (victim / "fixture").write_text("unrelated user data")
        digest = self.scratch_digest(scratch)
        unlink = os.unlink
        calls = []

        def swapped(path, *args, **kwargs):
            if not calls:
                calls.append(1)
                scratch.rename(owned / "moved")
                scratch.symlink_to(victim, target_is_directory=True)
            return unlink(path, *args, **kwargs)

        with mock.patch.object(kg.os, "unlink", side_effect=swapped):
            self.in_process("delete-scratch", "--path", scratch, "--root", owned,
                            "--expect", digest, outcome="retained", contains="changed before unlink")
        self.assertEqual((victim / "fixture").read_text(), "unrelated user data")
        self.assertFalse((owned / "moved/fixture").exists())

    def test_nested_scratch_fd_traversal(self):
        owned = self.root / "owned"
        scratch = owned / "nested/scratch"
        for relative in ("a/a/file", "a/b/file", "b/a/file", "scratch/fixture"):
            path = scratch / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(relative)
        digest = self.scratch_digest(scratch)
        self.cli("delete-scratch", "--path", scratch, "--root", owned, "--expect", digest)
        self.assertFalse(scratch.exists())
        self.assertTrue((owned / "nested").is_dir())

    @unittest.skipUnless(resource is not None, "requires POSIX descriptor limits")
    def test_wide_scratch_tree_under_256_fd_limit_is_complete_and_idempotent(self):
        owned = self.root / "owned"
        scratch = owned / "scratch"
        scratch.mkdir(parents=True)
        for index in range(400):
            directory = scratch / ("d%03d" % index)
            directory.mkdir()
            (directory / "fixture").write_text("owned fixture %d" % index)
        digest = self.scratch_digest(scratch)
        for outcome in ("done", "absent"):
            self.cli("delete-scratch", "--path", scratch, "--root", owned, "--expect", digest,
                     fd_limit=256, outcome=outcome)
            self.assertFalse(scratch.exists())
            self.assertEqual(list(owned.iterdir()), [])

    def path_aliases(self):
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        paths = [alias, self.raw_root]
        if (sys.platform == "darwin" and Path("/var").is_symlink()
                and Path("/private/var") in self.root.parents):
            paths.append(Path("/var") / self.root.relative_to("/private/var"))
        return paths

    def test_canonical_worktree_aliases_include_macos_var_tmpdir(self):
        aliases = self.path_aliases()
        for index, alias in enumerate(aliases):
            name = "missing-" + str(index)
            path = self.root / name
            self.git("worktree", "add", "--detach", str(alias / name), self.base)
            shutil.rmtree(path)
            self.cli("remove-worktree", "--path", alias / name, outcome="retained", contains="metadata")
            self.assertIn(str(path), self.git("worktree", "list", "--porcelain").stdout)
        existing = self.detached("existing")
        self.cli("remove-worktree", "--path", aliases[0] / existing.name)
        self.assertFalse(existing.exists())
        self.cli("remove-worktree", "--path", aliases[0] / "repo", outcome="retained", contains="main worktree")

    def test_canonical_scratch_aliases_include_macos_var_tmpdir(self):
        for index, alias in enumerate(self.path_aliases()):
            name = "owned-" + str(index)
            owned = self.root / name
            owned.mkdir()
            scratch = owned / "scratch"
            scratch.write_text("ephemeral")
            digest = self.scratch_digest(scratch)
            self.assertEqual(self.scratch_digest(alias / name / "scratch"), digest)
            self.cli("delete-scratch", "--path", alias / name / "scratch", "--root", alias / name,
                     "--expect", digest)
            self.assertFalse(scratch.exists())

    def test_inaccessible_parent_is_error_not_absence(self):
        parent = self.root / "inaccessible"
        parent.mkdir()
        path = parent / "existing"
        path.mkdir()
        parent.chmod(0)
        try:
            try:
                path.lstat()
            except PermissionError:
                pass
            else:
                self.skipTest("test requires an unprivileged uid enforcing EACCES")
            self.cli("remove-worktree", "--path", path, outcome="error")
            self.cli("delete-scratch", "--path", path, "--root", self.root,
                     "--expect", "not-an-absence-proof", outcome="error")
        finally:
            parent.chmod(0o700)
        self.assertTrue(path.is_dir())

    def test_worktree_symlink_leaf_cannot_remove_another_worktree(self):
        first, second = self.detached("wtA"), self.detached("wtB")
        outside = self.root / "outside/child"
        outside.mkdir(parents=True)
        ancestor = self.root / "ancestor"
        ancestor.symlink_to(outside, target_is_directory=True)
        # Resolve the parent before '..', rather than lexically collapsing it
        # onto the unrelated registered wtB in self.root.
        self.cli("remove-worktree", "--path", ancestor / "../wtB", outcome="absent")
        self.assertTrue(second.is_dir())
        alias = self.root / "link"
        alias.symlink_to(second, target_is_directory=True)
        self.cli("remove-worktree", "--path", alias, outcome="retained", contains="not a registered")
        self.assertTrue(second.is_dir())
        self.assertTrue(alias.is_symlink())
        shutil.rmtree(first)
        first.symlink_to(second, target_is_directory=True)
        self.cli("remove-worktree", "--path", first, outcome="retained", contains="uninspectable")
        self.assertTrue(first.is_symlink())
        self.assertTrue((second / "product.md").is_file())
        entries = self.git("worktree", "list", "--porcelain").stdout
        self.assertIn("worktree " + str(first) + "\n", entries)
        self.assertIn("worktree " + str(second) + "\n", entries)

    def test_empty_path_and_root_are_errors_before_any_mutation(self):
        worktree = self.detached()
        self.cli("remove-worktree", "--path", "", "--expect-head", self.base,
                 cwd=worktree, outcome="error", contains="empty")
        self.assertTrue((worktree / "product.md").is_file())
        self.assertIn(str(worktree), self.git("worktree", "list", "--porcelain").stdout)
        owned = self.root / "owned"
        scratch = owned / "scratch"
        scratch.mkdir(parents=True)
        file = scratch / "fixture"
        file.write_text("owned fixture")
        directory_digest, file_digest = self.scratch_digest(scratch), self.scratch_digest(file)
        self.cli("scratch-digest", "--path", "", cwd=scratch, outcome="error", contains="empty")
        self.cli("delete-scratch", "--path", "", "--root", owned, "--expect", directory_digest,
                 cwd=scratch, outcome="error", contains="empty")
        self.cli("delete-scratch", "--path", file, "--root", "", "--expect", file_digest,
                 cwd=owned, outcome="error", contains="empty")
        self.assertTrue(file.is_file())
        self.assertEqual(self.scratch_digest(scratch), directory_digest)

    def test_empty_expect_head_is_invalid_not_omitted(self):
        path = self.detached()
        tip = self.commit("extra", "unique worktree commit", cwd=path)
        self.cli("remove-worktree", "--path", path, "--expect-head", "", outcome="error", contains="invalid SHA")
        self.assertTrue(path.is_dir())
        self.assertEqual(self.tip(cwd=path), tip)

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

    def fake_gh(self, head=None, merge=None, polls=1, initial="OPEN",
                poll_head=None, poll_base=None, poll_state=None):
        self.gh_state = self.root / "gh-state.json"
        self.gh_state.write_text(json.dumps(dict(head=head or self.base, merge=merge or self.base,
                                                 polls=polls, state=initial, calls=[], requested=False,
                                                 base="main", poll_head=poll_head,
                                                 poll_base=poll_base, poll_state=poll_state)))
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
        for field in ('head', 'base', 'state'):
            if s['poll_' + field] is not None:
                s[field] = s['poll_' + field]
    print(json.dumps(dict(state=s['state'], headRefOid=s['head'],
                         mergeCommit={'oid': s['merge']}, baseRefName=s['base'])))
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
        (self.repo / ".kstack").mkdir()
        (self.repo / ".kstack/project.json").write_text('{"finish":{"allow_merge":true}}')
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

    def test_merge_rejects_merged_and_closed_start_states(self):
        for state in ("MERGED", "CLOSED"):
            with self.subTest(state=state):
                self.fake_gh(initial=state)
                self.merge_cli("--user-consented", outcome="error", contains="not OPEN")
                api = json.loads(self.gh_state.read_text())
                self.assertFalse(api["requested"])
                self.assertEqual(len(api["calls"]), 1)

    def test_merge_rejects_head_and_base_changes_during_poll(self):
        changed = self.commit("changed-head", "not the verified PR head")
        for change in (dict(poll_head=changed), dict(poll_base="other-base")):
            with self.subTest(change=change):
                self.fake_gh(**change)
                self.merge_cli("--user-consented", outcome="error", contains="head/base changed")
                self.assertTrue(json.loads(self.gh_state.read_text())["requested"])

    def test_merge_closed_during_poll_is_not_a_timeout(self):
        self.fake_gh(poll_state="CLOSED")
        self.merge_cli("--user-consented", outcome="error", contains="closed without merge")
        self.assertEqual(len(json.loads(self.gh_state.read_text())["calls"]), 3)

    def test_negative_pr_merge_mappings_retain_unique_branch(self):
        self.git("switch", "-c", "worker")
        tip = self.commit("unique", "unmerged worker change")
        self.git("switch", "main")
        self.git("config", "branch.worker.note", "preserve with branch")
        before = self.branch_config("worker")
        cases = (dict(head=tip, merge=self.base, initial="OPEN"),
                 dict(head=tip, merge=self.base, initial="CLOSED"),
                 dict(head=self.base, merge=self.base, initial="MERGED"),
                 dict(head=tip, merge=tip, initial="MERGED"))
        for mapping in cases:
            with self.subTest(mapping=mapping):
                self.fake_gh(**mapping)
                self.local_delete(expect=tip, extra=("--pr", "7", "--config-digest", self.config_digest()),
                                  outcome="retained", contains="PR merge mapping unproven")
                self.assertEqual(self.tip("worker"), tip)
                self.assertEqual(self.branch_config("worker"), before)

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
