"""promote-skill.py must mirror plugin-root directories to a SECOND destination
root. comment-reviewer is the first plugin in the catalog that is more than a
skill, and without this its hook, agent, command, and manifest never reach the
marketplace -- the gate would simply not exist for anyone who installs it."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path.home() / ".claude/skills/kettle-skill-creator/scripts/promote-skill.py"


def build_source(tmp_path):
    src = tmp_path / "src" / "demo-plugin"
    (src / "references").mkdir(parents=True)
    (src / "scripts").mkdir()
    (src / "agents").mkdir()
    (src / "hooks" / "scripts").mkdir(parents=True)
    (src / "commands").mkdir()
    (src / "tests").mkdir()
    (src / ".claude-plugin").mkdir()
    (src / "SKILL.md").write_text("---\nname: demo-plugin\ndescription: d\n---\n\nBody\n")
    (src / "references" / "r.md").write_text("r\n")
    (src / "scripts" / "s.py").write_text("s\n")
    (src / "agents" / "a.md").write_text("a\n")
    (src / "hooks" / "hooks.json").write_text('{"hooks": {}}\n')
    (src / "hooks" / "scripts" / "g.py").write_text("g\n")
    (src / "commands" / "c.md").write_text("c\n")
    (src / "tests" / "test_x.py").write_text("x\n")
    (src / ".claude-plugin" / "plugin.json").write_text('{"name": "demo-plugin"}\n')
    return src.parent


def build_repo(tmp_path):
    repo = tmp_path / "market"
    (repo / "plugins").mkdir(parents=True)
    (repo / ".claude-plugin").mkdir()
    (repo / "justfile").write_text("")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def promote(repo, source_root, name="demo-plugin", extra=()):
    return subprocess.run(
        [sys.executable, str(SCRIPT), name, "--source", str(source_root),
         "--categories", "claude-tooling", *extra],
        cwd=repo, capture_output=True, text=True,
    )


def test_skill_content_lands_under_skills(tmp_path):
    source_root, repo = build_source(tmp_path), build_repo(tmp_path)
    assert promote(repo, source_root).returncode == 0
    skill = repo / "plugins" / "demo-plugin" / "skills" / "demo-plugin"
    assert (skill / "SKILL.md").is_file()
    assert (skill / "references" / "r.md").is_file()
    assert (skill / "scripts" / "s.py").is_file()


def test_plugin_root_dirs_land_at_the_plugin_root(tmp_path):
    source_root, repo = build_source(tmp_path), build_repo(tmp_path)
    assert promote(repo, source_root).returncode == 0
    root = repo / "plugins" / "demo-plugin"
    assert (root / "agents" / "a.md").is_file()
    assert (root / "hooks" / "hooks.json").is_file()
    assert (root / "hooks" / "scripts" / "g.py").is_file()
    assert (root / "commands" / "c.md").is_file()
    assert (root / "tests" / "test_x.py").is_file()
    assert (root / ".claude-plugin" / "plugin.json").is_file()
    assert not (root / "skills" / "demo-plugin" / "agents").exists()


def test_plugin_root_dirs_are_mirrored_not_copied_once(tmp_path):
    """A file deleted from the source must disappear from the marketplace."""
    source_root, repo = build_source(tmp_path), build_repo(tmp_path)
    promote(repo, source_root)
    (source_root / "demo-plugin" / "agents" / "a.md").unlink()
    (source_root / "demo-plugin" / "agents" / "b.md").write_text("b\n")
    assert promote(repo, source_root).returncode == 0
    root = repo / "plugins" / "demo-plugin"
    assert not (root / "agents" / "a.md").exists()
    assert (root / "agents" / "b.md").is_file()


def test_config_yaml_is_still_preserved(tmp_path):
    source_root, repo = build_source(tmp_path), build_repo(tmp_path)
    promote(repo, source_root)
    config = repo / "plugins" / "demo-plugin" / "skills" / "demo-plugin" / "config.yaml"
    config.write_text("categories:\n  - claude-tooling\n  - devops\n")
    promote(repo, source_root)
    assert "devops" in config.read_text()


def test_executable_bit_survives_promotion(tmp_path):
    source_root, repo = build_source(tmp_path), build_repo(tmp_path)
    gate = source_root / "demo-plugin" / "hooks" / "scripts" / "g.py"
    gate.chmod(0o755)
    promote(repo, source_root)
    import os
    promoted = repo / "plugins" / "demo-plugin" / "hooks" / "scripts" / "g.py"
    assert os.access(promoted, os.X_OK)


def test_skill_only_plugin_gains_no_empty_dirs(tmp_path):
    """Regression guard for the other 60+ plugins in the catalog."""
    source_root = tmp_path / "src2"
    plain = source_root / "plain-skill"
    plain.mkdir(parents=True)
    (plain / "SKILL.md").write_text("---\nname: plain-skill\ndescription: d\n---\n\nB\n")
    repo = build_repo(tmp_path)
    assert promote(repo, source_root, name="plain-skill").returncode == 0
    root = repo / "plugins" / "plain-skill"
    for name in ("agents", "hooks", "commands", "tests", ".claude-plugin"):
        assert not (root / name).exists()
