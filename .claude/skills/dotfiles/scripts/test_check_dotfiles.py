#!/usr/bin/env python3
"""Tests for check_dotfiles.py. Run: python3 test_check_dotfiles.py"""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "check_dotfiles", Path(__file__).with_name("check_dotfiles.py"))
cd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cd)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.package = root / "dotfiles"
        self.home = root / "home"
        (self.package / ".config").mkdir(parents=True)
        self.home.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text="x"):
        path = self.package / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def link(self, rel):
        """Link home/rel -> package/rel the way stow would."""
        target = self.home / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(os.path.relpath(self.package / rel, target.parent))


class TestIgnore(Fixture):
    def test_basename_pattern_prunes_every_level(self):
        (self.package / ".stow-local-ignore").write_text("dev\n")
        self.write("dev/tool.sh")
        self.write(".config/keep.conf")
        found = set(walk(self))
        self.assertIn(Path(".config/keep.conf"), found)
        self.assertNotIn(Path("dev/tool.sh"), found)

    def test_anchored_path_pattern_matches_only_repo_root(self):
        (self.package / ".stow-local-ignore").write_text(r"^/AGENTS\.md$" + "\n")
        self.write("AGENTS.md")
        self.write(".config/AGENTS.md")
        found = set(walk(self))
        self.assertNotIn(Path("AGENTS.md"), found)
        self.assertIn(Path(".config/AGENTS.md"), found,
                      "anchored pattern must not prune nested files of the same name")

    def test_comments_and_blank_lines_ignored(self):
        (self.package / ".stow-local-ignore").write_text("# a comment\n\ndev\n")
        self.write("dev/x")
        self.write("keep")
        self.assertEqual({Path("keep")}, set(walk(self)))


class TestDrift(Fixture):
    def test_symlink_into_repo_is_clean(self):
        (self.package / ".stow-local-ignore").write_text("")
        self.write(".zshrc")
        self.link(".zshrc")
        shadowed, foreign = cd.check_drift(self.package, self.home)
        self.assertEqual([], shadowed)
        self.assertEqual([], foreign)

    def test_real_file_in_home_is_shadowed(self):
        (self.package / ".stow-local-ignore").write_text("")
        self.write(".zshrc")
        (self.home / ".zshrc").write_text("drifted copy")
        shadowed, _ = cd.check_drift(self.package, self.home)
        self.assertEqual([Path(".zshrc")], shadowed)

    def test_missing_target_is_not_reported_as_drift(self):
        (self.package / ".stow-local-ignore").write_text("")
        self.write(".config/never-stowed.conf")
        shadowed, foreign = cd.check_drift(self.package, self.home)
        self.assertEqual([], shadowed)
        self.assertEqual([], foreign)

    def test_folded_directory_symlink_is_clean(self):
        """stow folds whole directories when it can; files beneath a folded
        directory are not symlinks but are still correctly stowed."""
        (self.package / ".stow-local-ignore").write_text("")
        self.write(".claude/skills/dotfiles/SKILL.md")
        (self.home / ".claude").mkdir(parents=True)
        (self.home / ".claude/skills").symlink_to(self.package / ".claude/skills")
        shadowed, foreign = cd.check_drift(self.package, self.home)
        self.assertEqual([], shadowed, "folded directory must not read as drift")
        self.assertEqual([], foreign)

    def test_symlink_pointing_outside_repo_is_flagged_separately(self):
        (self.package / ".stow-local-ignore").write_text("")
        self.write(".config/ghostty/themes")
        elsewhere = Path(self.tmp.name) / "elsewhere"
        elsewhere.mkdir()
        (self.home / ".config" / "ghostty").mkdir(parents=True)
        (self.home / ".config/ghostty/themes").symlink_to(elsewhere)
        shadowed, foreign = cd.check_drift(self.package, self.home)
        self.assertEqual([], shadowed)
        self.assertEqual([Path(".config/ghostty/themes")], foreign)


class TestOverlap(Fixture):
    def test_chezmoi_target_that_is_a_stow_symlink_conflicts(self):
        (self.package / ".stow-local-ignore").write_text("")
        self.write(".zshrc")
        self.link(".zshrc")
        conflicts = cd.check_overlap(self.package, self.home,
                                     managed=[Path(".zshrc")])
        self.assertEqual(1, len(conflicts))
        self.assertIn("stow symlink", conflicts[0][1])

    def test_path_present_in_both_trees_conflicts(self):
        (self.package / ".stow-local-ignore").write_text("")
        self.write(".gitconfig")
        conflicts = cd.check_overlap(self.package, self.home,
                                     managed=[Path(".gitconfig")])
        self.assertEqual(1, len(conflicts))
        self.assertIn("stow package", conflicts[0][1])

    def test_disjoint_ownership_is_clean(self):
        (self.package / ".stow-local-ignore").write_text("")
        self.write(".zshrc")
        self.link(".zshrc")
        conflicts = cd.check_overlap(self.package, self.home,
                                     managed=[Path(".config/secret.toml")])
        self.assertEqual([], conflicts)

    def test_missing_chezmoi_returns_none(self):
        self.assertIsNone(cd.check_overlap(self.package, self.home, managed=None)
                          if cd.chezmoi_managed(self.home) is None else None)


def walk(case):
    return cd.walk_package(case.package)


if __name__ == "__main__":
    unittest.main(verbosity=2)
