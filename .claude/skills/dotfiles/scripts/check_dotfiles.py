#!/usr/bin/env python3
"""Guard the two failure modes of a stow + chezmoi dotfiles repo.

drift    A file the repo tracks is a *real file* in $HOME instead of a stow
         symlink. Installers that write with `mv tmp target` (omarchy's
         migrations do this) silently replace a symlink, after which your edits
         land on a detached copy and the repo copy goes stale.

overlap  A path is claimed by both managers. `chezmoi apply` writes real files
         and will overwrite a stow symlink; `stow -R` will then conflict with
         what chezmoi wrote. They coexist only while they own disjoint paths.

Exit 0 when clean, 1 when something needs attention.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# GNU stow's built-in list, used only when the package has no .stow-local-ignore
# (a present ignore file replaces this list entirely rather than extending it).
DEFAULT_IGNORE = [
    r"RCS", r".+,v", r"CVS", r"\.\#.+", r"\.cvsignore", r"\.svn", r"_darcs",
    r"\.hg", r"\.git", r"\.gitignore", r"\.gitmodules", r".+~", r"\.\#.*",
    r"README.*", r"LICENSE.*", r"COPYING",
]


def load_ignore(package: Path):
    """Parse .stow-local-ignore into (path_regexes, basename_regexes).

    stow anchors every pattern. A pattern containing "/" matches the path
    relative to the package root with a leading slash; every other pattern
    matches any single path segment.
    """
    ignore_file = package / ".stow-local-ignore"
    lines = DEFAULT_IGNORE
    if ignore_file.is_file():
        lines = []
        for raw in ignore_file.read_text().splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                lines.append(line)

    paths, names = [], []
    for pattern in lines:
        try:
            compiled = re.compile("^(?:" + pattern + ")$")
        except re.error:
            continue
        (paths if "/" in pattern else names).append(compiled)
    return paths, names


def is_ignored(rel: Path, path_res, name_res) -> bool:
    if any(r.match("/" + rel.as_posix()) for r in path_res):
        return True
    # stow tests each segment, so ignoring "dev" prunes the whole subtree.
    return any(r.match(part) for part in rel.parts for r in name_res)


# stow never stows its own ignore files, whatever the ignore list says.
IMPLICIT_IGNORE = {Path(".stow-local-ignore"), Path(".stow-global-ignore")}


def walk_package(package: Path):
    """Yield paths relative to the package root, honouring the ignore list."""
    path_res, name_res = load_ignore(package)
    for dirpath, dirnames, filenames in os.walk(package):
        rel_dir = Path(dirpath).relative_to(package)
        dirnames[:] = [
            d for d in dirnames
            if not is_ignored(rel_dir / d if rel_dir != Path(".") else Path(d),
                              path_res, name_res)
        ]
        for name in filenames:
            rel = (rel_dir / name) if rel_dir != Path(".") else Path(name)
            if rel in IMPLICIT_IGNORE:
                continue
            if not is_ignored(rel, path_res, name_res):
                yield rel


def resolves_into(link: Path, root: Path) -> bool:
    try:
        return root.resolve() in link.resolve().parents
    except OSError:
        return False


def check_drift(package: Path, home: Path):
    """Repo-tracked paths whose $HOME counterpart is a real file, not a link.

    Compares *resolved* paths rather than testing the leaf for symlink-ness,
    because stow folds whole directories when it can: with ~/.claude/skills a
    directory symlink, the files beneath it are not symlinks themselves yet are
    still correctly stowed.
    """
    shadowed, foreign = [], []
    for rel in walk_package(package):
        target = home / rel
        if not target.is_symlink() and not target.exists():
            continue  # not stowed at all -- a different situation from drift
        try:
            if target.resolve() == (package / rel).resolve():
                continue  # linked directly, or via a folded parent directory
        except OSError:
            continue
        (foreign if target.is_symlink() else shadowed).append(rel)
    return shadowed, foreign


def chezmoi_managed(home: Path):
    """Managed target paths, or None when chezmoi is not installed."""
    try:
        out = subprocess.run(["chezmoi", "managed"], capture_output=True,
                             text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return [Path(line.strip()) for line in out.stdout.splitlines() if line.strip()]


def check_overlap(package: Path, home: Path, managed=None):
    """Paths claimed by chezmoi that stow also owns."""
    if managed is None:
        managed = chezmoi_managed(home)
    if managed is None:
        return None

    stow_owned = set(walk_package(package))
    conflicts = []
    for rel in managed:
        target = home / rel
        if target.is_symlink() and resolves_into(target, package):
            conflicts.append((rel, "chezmoi target is a stow symlink"))
        elif rel in stow_owned:
            conflicts.append((rel, "path exists in the stow package too"))
    return conflicts


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("check", choices=["drift", "overlap", "all"], nargs="?",
                        default="all")
    parser.add_argument("--package", default=os.path.expanduser("~/dotfiles"),
                        help="stow package root (default: ~/dotfiles)")
    parser.add_argument("--home", default=os.path.expanduser("~"),
                        help="stow target directory (default: ~)")
    args = parser.parse_args()

    package, home = Path(args.package), Path(args.home)
    if not package.is_dir():
        print("no such package directory: %s" % package, file=sys.stderr)
        return 2

    failed = False

    if args.check in ("drift", "all"):
        shadowed, foreign = check_drift(package, home)
        if shadowed:
            failed = True
            print("SHADOWED -- real files in $HOME where the repo expects a symlink:")
            for rel in sorted(shadowed):
                print("  %s" % rel)
            print("  fix: stow -d %s -t %s -n -v --adopt .   (drop -n to apply,"
                  " then review git diff)" % (package, home))
        if foreign:
            print("NOTE -- symlinks pointing outside the repo (usually fine):")
            for rel in sorted(foreign):
                print("  %s" % rel)
        if not shadowed:
            print("drift: clean")

    if args.check in ("overlap", "all"):
        conflicts = check_overlap(package, home)
        if conflicts is None:
            print("overlap: skipped (chezmoi not installed or no source state)")
        elif conflicts:
            failed = True
            print("OVERLAP -- both managers claim these paths:")
            for rel, why in sorted(conflicts):
                print("  %s  (%s)" % (rel, why))
            print("  fix: chezmoi forget <path>, or remove it from the stow package."
                  " One owner per path.")
        else:
            print("overlap: clean")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
