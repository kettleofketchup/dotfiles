import pytest
import prmatch


@pytest.mark.parametrize("command", [
    "gh pr create",
    "gh pr create --fill",
    "gh pr create --title 'x' --body 'y'",
    "fj pr create",
    "fj -H codeberg.org pr create",          # option VALUE must not shift the pair
    "glab mr create --fill",
    "mj pr create",
    "PAGER= gh pr create",                    # leading assignment stripped
    "env GH_TOKEN=x gh pr create",            # `env` prefix stripped
    "gh  pr   create",                        # extra whitespace
    "git push && gh pr create",               # later segment
    "gh pr list; gh pr create",
    "make build || gh pr create --draft",
    # Shell metacharacters INSIDE quotes. Splitting the raw string first cuts
    # through the quotes and loses the invocation entirely -- these are the cases
    # that make the difference between a working gate and a decorative one.
    'gh pr create --title "fix; refactor"',
    'gh pr create --body "a|b"',
    'gh pr create --title "A && B"',
    'gh pr create --title t --body "line one\nline two"',
    # A skip on a DIFFERENT segment must not release this one.
    "CLAUDE_SKIP_COMMENT_REVIEW=1 ls; gh pr create",
    "gh pr create && CLAUDE_SKIP_COMMENT_REVIEW=1 echo x",
])
def test_matches_real_invocations(command):
    assert prmatch.matches(command)


@pytest.mark.parametrize("command", [
    'git commit -m "prep for gh pr create"',  # the guard the spec requires
    'echo "run gh pr create next"',
    "gh pr list",
    "gh pr view 12",
    "gh issue create --title 'pr create'",
    "gh alias set prc 'pr create'",
    "gh repo create",
    "git pr create",                          # not a forge CLI
    "cat <<EOF\ngh pr create\nEOF",           # heredoc body is data
    "cat <<'EOF'\ngh pr create\nEOF",
    "# gh pr create",                         # commented out
    "gh pr create --help",                    # help text, not a creation
])
def test_does_not_match(command):
    assert not prmatch.matches(command)


def test_unbalanced_quotes_pass_through_rather_than_raising():
    """shlex raises on unbalanced quotes; the gate must never crash the turn."""
    assert prmatch.matches('gh pr create --title "unclosed') is False


@pytest.mark.parametrize("command", [
    "CLAUDE_SKIP_COMMENT_REVIEW=1 gh pr create",
    "CLAUDE_SKIP_COMMENT_REVIEW=true gh pr create --fill",
])
def test_skip_assignment_in_the_command_is_detected(command):
    """An env var set on the inspected command never reaches the hook process,
    so the assignment must be read out of the command string itself."""
    assert prmatch.wants_skip(command)


def test_skip_not_detected_when_absent():
    assert not prmatch.wants_skip("gh pr create")


def test_skip_zero_is_not_a_skip():
    assert not prmatch.wants_skip("CLAUDE_SKIP_COMMENT_REVIEW=0 gh pr create")


def test_skip_is_segment_local():
    """A shell assignment applies only to the command it prefixes."""
    assert not prmatch.matches("CLAUDE_SKIP_COMMENT_REVIEW=1 gh pr create")
    assert prmatch.matches("CLAUDE_SKIP_COMMENT_REVIEW=1 ls; gh pr create")


def test_quoted_metacharacters_do_not_hide_the_invocation():
    """Regression: the splitter used to run before the lexer, so a quoted ';'
    produced two unbalanced halves and the gate saw nothing."""
    for command in ('gh pr create --title "fix; refactor"',
                    'gh pr create --body "a|b"',
                    'gh pr create --body "one\ntwo"'):
        assert prmatch.segments(command), command
        assert prmatch.matches(command), command
