import sys
sys.dont_write_bytecode = True
import importlib.machinery
import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "chezmoi/dot_local/bin/executable_herdr-agent-labels"
loader = importlib.machinery.SourceFileLoader("herdr_agent_labels", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
hal = importlib.util.module_from_spec(spec)
loader.exec_module(hal)


def test_project_dir_encodes_like_claude(tmp_path):
    got = hal.project_dir("/home/k/git_repos/a.b_c/.claude", root=tmp_path)
    assert got == tmp_path / "-home-k-git-repos-a-b-c--claude"


def test_extract_takes_latest_branch_and_pr():
    entries = [
        {"gitBranch": "main", "message": {"content": "see https://github.com/o/r/pull/12"}},
        {"gitBranch": "feat/750-mmr", "message": {"content": "opened https://github.com/o/r/pull/802"}},
        {"gitBranch": "", "type": "summary"},
    ]
    assert hal.extract(entries) == ("feat/750-mmr", "#802")


def test_extract_gitlab_merge_request():
    entries = [{"gitBranch": "fix/x", "message": {"content": "https://gitlab.graynet.lan/inf/flakes/os.flake/-/merge_requests/17"}}]
    assert hal.extract(entries) == ("fix/x", "!17")


def test_extract_nothing_found():
    assert hal.extract([{"type": "summary"}]) == (None, None)


def test_read_tail_skips_partial_first_line(tmp_path):
    p = tmp_path / "s.jsonl"
    lines = [json.dumps({"n": i, "pad": "x" * 50}) for i in range(100)]
    p.write_text("\n".join(lines) + "\n")
    got = hal.read_tail(p, limit=500)
    assert got
    assert got[-1]["n"] == 99
    assert all(isinstance(e, dict) for e in got)


def test_read_tail_missing_file(tmp_path):
    assert hal.read_tail(tmp_path / "nope.jsonl") == []


def test_find_transcript_falls_back_to_any_project(tmp_path):
    other = tmp_path / "-somewhere-else"
    other.mkdir()
    (other / "abc.jsonl").write_text("{}\n")
    assert hal.find_transcript("/home/k/moved", "abc", root=tmp_path) == other / "abc.jsonl"
    assert hal.find_transcript("/home/k/moved", "zzz", root=tmp_path) is None
