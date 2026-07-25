"""The marketplace validator enforces these limits repo-wide. Catching them here
means a promotion never lands a plugin that fails validation.

Paths come from paths.py, not from ROOT: after promotion SKILL.md and references/
move under skills/<name>/ while tests/ stays at the plugin root, and `just test`
runs the promoted tree.
"""

import paths

MAX_BODY_LINES = 150
MAX_DESCRIPTION_CHARS = 200
REQUIRED_REFERENCES = {"comment-classes.md", "never-touch.md", "rewrite-guidelines.md"}


def skill_text():
    assert paths.SKILL_MD.is_file(), f"SKILL.md not found at {paths.SKILL_MD}"
    return paths.SKILL_MD.read_text()


def frontmatter_and_body(text):
    assert text.startswith("---\n")
    _, front, body = text.split("---\n", 2)
    return front, body


def test_the_three_references_exist():
    """The class rules and both never-touch tiers live only in these files. The
    loop-based tests below pass on an empty directory, so this one carries them."""
    assert {p.name for p in paths.REFERENCES.glob("*.md")} == REQUIRED_REFERENCES


def test_skill_frontmatter_name_matches_the_directory():
    front, _ = frontmatter_and_body(skill_text())
    assert "name: comment-reviewer" in front


def test_skill_description_fits_the_validator_limits():
    front, _ = frontmatter_and_body(skill_text())
    line = next(l for l in front.splitlines() if l.startswith("description:"))
    description = line.split("description:", 1)[1].strip()
    assert 0 < len(description) <= MAX_DESCRIPTION_CHARS
    assert "<" not in description and ">" not in description


def test_skill_body_is_within_the_line_budget():
    _, body = frontmatter_and_body(skill_text())
    assert len(body.splitlines()) <= MAX_BODY_LINES


def test_every_reference_is_within_the_line_budget():
    for reference in paths.REFERENCES.glob("*.md"):
        assert len(reference.read_text().splitlines()) <= MAX_BODY_LINES, reference


def test_skill_documents_the_group_install_limitation():
    assert "comment-reviewer@kettleofskills" in skill_text()


def test_references_are_all_linked_from_the_skill():
    body = skill_text()
    for reference in paths.REFERENCES.glob("*.md"):
        assert reference.name in body, f"{reference.name} is unreachable"
