"""Decide whether a shell command creates a pull or merge request.

Tokenised, never a substring regex. `git commit -m "prep for gh pr create"`
contains the phrase but creates nothing, and denying it would be worse than
missing a real invocation.

Known and accepted blind spots: `gh api .../pulls -X POST`, user-defined `gh`
aliases, the web UI, and wrapper recipes such as `just pr`.
"""

import re
import shlex

SKIP_VAR = "CLAUDE_SKIP_COMMENT_REVIEW"
FORGE_CLIS = frozenset({"gh", "fj", "mj", "glab"})
REQUEST_NOUNS = frozenset({"pr", "mr"})
CREATE_VERB = "create"

_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_SEGMENT_OPERATORS = frozenset({";", "&&", "||", "|", "&", "\n"})
_HEREDOC_START = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
_SKIP_TRUTHY = frozenset({"1", "true", "yes", "on"})
# `--help` prints usage and creates nothing; denying it is pure friction.
_NON_CREATING_FLAGS = frozenset({"--help", "-h"})


def strip_heredocs(command):
    """Remove heredoc bodies. Their contents are data, not commands -- a body
    mentioning `gh pr create` must not trigger the gate."""
    lines = command.split("\n")
    kept, index = [], 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        match = _HEREDOC_START.search(line)
        index += 1
        if not match:
            continue
        delimiter = match.group(2)
        while index < len(lines) and lines[index].strip() != delimiter:
            index += 1
        index += 1  # drop the delimiter line too
    return "\n".join(kept)


def segments(command):
    """Token lists for each independently-executed part of the command.

    Lexes FIRST, then splits on operator tokens. Splitting the raw string first
    cuts straight through quotes: `gh pr create --title "fix; refactor"` becomes
    two unbalanced halves, shlex raises on both, and a genuine PR creation goes
    invisible to the gate. A multi-line `--body` fails the same way, and both are
    mainline invocation shapes.
    """
    lexer = shlex.shlex(strip_heredocs(command), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    out, current = [], []
    try:
        for token in lexer:
            if token in _SEGMENT_OPERATORS:
                if current:
                    out.append(current)
                current = []
            else:
                current.append(token)
    except ValueError:
        return []  # unbalanced quotes: unmatchable, never raise
    if current:
        out.append(current)
    return out


def _drop_env_prefix(tokens):
    index = 0
    while index < len(tokens) and (_ASSIGNMENT.match(tokens[index]) or tokens[index] == "env"):
        index += 1
    return tokens[index:]


def is_pr_create(tokens):
    """True when these tokens invoke a forge CLI to create a PR or MR.

    Looks for an adjacent (pr|mr, create) token pair rather than the first two
    non-option arguments, because option values such as the host in
    `fj -H codeberg.org pr create` are not option-shaped.
    """
    tokens = _drop_env_prefix(tokens)
    if not tokens or tokens[0] not in FORGE_CLIS:
        return False
    if any(token in _NON_CREATING_FLAGS for token in tokens):
        return False
    rest = tokens[1:]
    return any(
        noun in REQUEST_NOUNS and verb == CREATE_VERB
        for noun, verb in zip(rest, rest[1:])
    )


def _has_skip(tokens):
    """True when this segment's own leading assignments request a skip.

    Reading it from the command string is the only thing that works: the hook is
    spawned by Claude Code and inherits Claude Code's environment, not the
    environment of the command being inspected.
    """
    for token in tokens:
        if not _ASSIGNMENT.match(token):
            return False
        name, _, value = token.partition("=")
        if name == SKIP_VAR and value.lower() in _SKIP_TRUTHY:
            return True
    return False


def wants_skip(command):
    return any(_has_skip(tokens) for tokens in segments(command))


def matches(command):
    """True when some segment creates a PR and that same segment carries no skip.

    Per-segment, because a shell assignment applies only to the command it
    prefixes: in `CLAUDE_SKIP_COMMENT_REVIEW=1 ls; gh pr create` the skip belongs
    to `ls`, and treating it as global would hand out a free bypass.
    """
    return any(
        is_pr_create(tokens) and not _has_skip(tokens) for tokens in segments(command)
    )
