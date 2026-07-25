"""Git repository fixtures. Every fixture builds a real repo -- these scripts
exist to handle git's actual layout quirks, which a mock would hide."""

import subprocess
import sys
from pathlib import Path

# Make paths.py importable before anything else, then put the script
# directories on sys.path using the layout it resolved.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import paths  # noqa: E402

for _candidate in (paths.SCRIPTS, paths.HOOK_SCRIPTS):
    if _candidate.is_dir():
        sys.path.insert(0, str(_candidate))

import pytest  # noqa: E402


def run(cwd, *args):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def empty_dir(tmp_path):
    d = tmp_path / "plain"
    d.mkdir()
    return d


@pytest.fixture
def repo(tmp_path):
    """Primary clone with one commit on main."""
    d = tmp_path / "repo"
    d.mkdir()
    run(d, "git", "init", "-q", "-b", "main")
    run(d, "git", "config", "user.email", "t@example.com")
    run(d, "git", "config", "user.name", "T")
    (d / "seed.txt").write_text("seed\n")
    run(d, "git", "add", "seed.txt")
    run(d, "git", "commit", "-q", "-m", "init")
    return d


@pytest.fixture
def repo_no_commits(tmp_path):
    d = tmp_path / "fresh"
    d.mkdir()
    run(d, "git", "init", "-q", "-b", "main")
    return d


@pytest.fixture
def worktree(repo):
    """Linked worktree: .git is a FILE holding a gitdir: pointer."""
    wt = repo.parent / "wt"
    run(repo, "git", "worktree", "add", "-q", str(wt), "-b", "feat")
    return wt


@pytest.fixture
def repo_master_only(tmp_path):
    """No remote; the only trunk-ish branch is `master` -- exercises the local
    fallback candidate list past `main`."""
    d = tmp_path / "master-repo"
    d.mkdir()
    run(d, "git", "init", "-q", "-b", "master")
    run(d, "git", "config", "user.email", "t@example.com")
    run(d, "git", "config", "user.name", "T")
    (d / "seed.txt").write_text("seed\n")
    run(d, "git", "add", "seed.txt")
    run(d, "git", "commit", "-q", "-m", "init")
    return d


@pytest.fixture
def cloned_without_symref(tmp_path):
    """origin/main exists as a remote-tracking ref, but refs/remotes/origin/HEAD
    has been deleted -- the symbolic-ref lookup must fail and fall through to
    the literal candidate list, which should still prefer the remote-tracking
    ref over the local branch of the same name.

    `git clone` only creates the origin/HEAD symref when the remote already has
    a resolvable HEAD at clone time, which requires seeding the bare repo with a
    commit *before* cloning it -- cloning an empty bare repo (as in
    cloned_with_remote, before its first push) creates no symref at all, so
    there is nothing here to delete unless the seed commit exists upfront."""
    seed = tmp_path / "seed"
    seed.mkdir()
    run(seed, "git", "init", "-q", "-b", "main")
    run(seed, "git", "config", "user.email", "t@example.com")
    run(seed, "git", "config", "user.name", "T")
    (seed / "a.txt").write_text("a\n")
    run(seed, "git", "add", "a.txt")
    run(seed, "git", "commit", "-q", "-m", "init")
    bare = tmp_path / "up.git"
    run(tmp_path, "git", "clone", "-q", "--bare", str(seed), str(bare))
    work = tmp_path / "work"
    run(tmp_path, "git", "clone", "-q", str(bare), str(work))
    run(work, "git", "symbolic-ref", "-d", "refs/remotes/origin/HEAD")
    return work


@pytest.fixture
def repo_no_trunk_candidate(tmp_path):
    """No remote, and no branch named main or master -- resolve_trunk has
    nothing to fall back to and must raise rather than guess."""
    d = tmp_path / "solo-repo"
    d.mkdir()
    run(d, "git", "init", "-q", "-b", "main")
    run(d, "git", "config", "user.email", "t@example.com")
    run(d, "git", "config", "user.name", "T")
    (d / "seed.txt").write_text("seed\n")
    run(d, "git", "add", "seed.txt")
    run(d, "git", "commit", "-q", "-m", "init")
    run(d, "git", "checkout", "-q", "-b", "solo")
    run(d, "git", "branch", "-D", "main")
    return d


@pytest.fixture
def cloned_with_remote(tmp_path):
    """origin/main exists and a feature branch has its own upstream set --
    the exact shape that makes @{u} the wrong base."""
    bare = tmp_path / "up.git"
    run(tmp_path, "git", "init", "-q", "-b", "main", "--bare", str(bare))
    work = tmp_path / "work"
    run(tmp_path, "git", "clone", "-q", str(bare), str(work))
    run(work, "git", "config", "user.email", "t@example.com")
    run(work, "git", "config", "user.name", "T")
    (work / "a.txt").write_text("a\n")
    run(work, "git", "add", "a.txt")
    run(work, "git", "commit", "-q", "-m", "init")
    run(work, "git", "push", "-q", "origin", "main")
    run(work, "git", "checkout", "-q", "-b", "feat")
    (work / "b.go").write_text("// hi\n")
    run(work, "git", "add", "b.go")
    run(work, "git", "commit", "-q", "-m", "feat")
    run(work, "git", "push", "-q", "-u", "origin", "feat")
    return work
