from datetime import datetime, timedelta, timezone

import gitpaths
import receipt

T0 = datetime(2026, 7, 25, 12, 0, tzinfo=timezone.utc)


def payload(**over):
    base = dict(
        commit_sha="c" * 40, tree_sha="t" * 40, base_sha="b" * 40,
        resolved_base_ref="origin/main", fixed={"A": 1, "B": 0, "C": 2},
        skipped=[], reported=[], partial=False, now=T0,
    )
    base.update(over)
    return receipt.build(**base)


def test_write_then_read_roundtrips(repo):
    receipt.write(repo, payload(), now=T0)
    root = gitpaths.receipt_root(repo)
    assert receipt.read(root, "t" * 40)["resolved_base_ref"] == "origin/main"


def test_write_names_the_file_after_the_tree_sha(repo):
    path = receipt.write(repo, payload(), now=T0)
    assert path.name == "t" * 40


def test_write_succeeds_in_a_worktree(worktree):
    """Guards the NotADirectoryError that a literal .git/ path would raise."""
    assert receipt.write(worktree, payload(), now=T0).is_file()


def test_read_returns_none_when_absent(repo):
    assert receipt.read(gitpaths.receipt_root(repo), "z" * 40) is None


def test_read_returns_none_on_unparseable_json(repo):
    root = gitpaths.receipt_root(repo)
    root.mkdir(parents=True, exist_ok=True)
    (root / ("t" * 40)).write_text("{not json")
    assert receipt.read(root, "t" * 40) is None


def test_is_valid_requires_matching_tree(repo):
    p = payload()
    assert receipt.is_valid(p, "t" * 40, "b" * 40, now=T0)
    assert not receipt.is_valid(p, "OTHER" + "t" * 35, "b" * 40, now=T0)


def test_is_valid_requires_matching_base(repo):
    """Retargeting the PR widens the touched-file set, so the old receipt must
    stop counting."""
    p = payload()
    assert not receipt.is_valid(p, "t" * 40, "different" + "b" * 31, now=T0)


def test_is_valid_expires_after_ttl(repo):
    p = payload()
    later = T0 + timedelta(days=receipt.TTL_DAYS + 1)
    assert not receipt.is_valid(p, "t" * 40, "b" * 40, now=later)


def test_prune_keeps_only_the_newest(repo):
    root = gitpaths.receipt_root(repo)
    for i in range(receipt.KEEP_NEWEST + 5):
        receipt.write(repo, payload(tree_sha=f"{i:040d}"), now=T0 + timedelta(minutes=i))
    receipt.prune(root, now=T0 + timedelta(hours=1))
    assert len(list(root.iterdir())) == receipt.KEEP_NEWEST
