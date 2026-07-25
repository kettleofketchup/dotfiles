#!/usr/bin/env python3
"""Extract comment spans from source files.

A character scanner per language, tracking string state, rather than line
regexes. The asymmetry that drives the design: missing a comment is a miss, but
mistaking a string literal for a comment means the reviewer edits live code. So
every ambiguity resolves toward skipping.

Reads newline-separated paths on stdin (not argv -- a wide rename can exceed
argv limits) and writes one JSON object on stdout.

Note: a path containing an embedded newline cannot be represented in this
protocol -- it fragments into multiple stdin lines, each looked up as its own
(almost certainly nonexistent) path. Out of scope: this is a limitation of the
newline-separated protocol itself, not something this module works around.
"""

import json
import re
import sys
from collections import namedtuple
from pathlib import Path

MAX_BYTES = 1_000_000
BINARY_SNIFF_BYTES = 8192

# line:       tokens that start a comment running to end of line
# block:      (open, close, nests) -- Rust nests /* */ by language rule, so the
#             first closer is not necessarily the end of the comment
# strings:    (open, close, escapes, multiline) -- escapes means a backslash
#             escapes the next character; multiline=False means a literal whose
#             closer is not on the same line is not a literal at all. Without
#             that, an apostrophe in YAML or HTML prose ("don't") opens a string
#             that swallows every comment in the rest of the file.
# docstrings: whether a 3-character string delimiter in docstring position is a
#             reviewable comment (Python) rather than data
# heredocs:   whether `<<[-]DELIM` / `<<[-]'DELIM'` / `<<[-]"DELIM"` opens a shell
#             heredoc whose body is skipped outright. The body is literal data
#             passed to a command, not shell syntax -- a `#` inside it is not a
#             comment, and scanning it as ordinary code would emit one anyway.
Lang = namedtuple("Lang", "line block strings docstrings heredocs", defaults=(False, False))

_C_STRINGS = (('"', '"', True, False), ("'", "'", True, False))

# A triple-quoted literal is a docstring only as the first statement of a module,
# class, or function. Anywhere else it is data, and rewriting it would change what
# the program does -- so the same delimiter has to be read two ways.
_DOCSTRING_OWNER = re.compile(r"^(async\s+def|def|class)\b")

# Reimplemented locally rather than imported from hooks/scripts/prmatch.py --
# that module installs to a different path and cannot be imported from here.
# Matches `<<EOF`, `<<-EOF`, `<<'EOF'`, `<<"EOF"`.
_HEREDOC_START = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def _skip_heredoc(text, index, match):
    """Index just past a heredoc body opened by `match` at `index`.

    The body runs from the line after the opener to the first line whose
    stripped content equals the delimiter (leading tabs, permitted by `<<-`,
    fall out of the strip along with everything else). A heredoc with no
    closing delimiter runs to end of file rather than raising -- the same
    "resolve toward skipping" rule as everywhere else in this module.
    """
    delimiter = match.group(2)
    length = len(text)
    line_end = text.find("\n", index)
    if line_end == -1:
        return length
    cursor = line_end + 1
    while True:
        next_nl = text.find("\n", cursor)
        segment_end = next_nl if next_nl != -1 else length
        segment = text[cursor:segment_end]
        if segment.strip() == delimiter or next_nl == -1:
            return segment_end + 1 if next_nl != -1 else length
        cursor = next_nl + 1


def _in_docstring_position(text, index):
    """True when the literal opening at `index` is a docstring, not data."""
    preceding = [line.strip() for line in text[:index].splitlines()]
    meaningful = [line for line in preceding if line and not line.startswith("#")]
    if not meaningful:
        return True  # module docstring, possibly preceded by comments
    last = meaningful[-1]
    return last.endswith(":") and bool(_DOCSTRING_OWNER.match(last))


# TOML basic strings (`"`, `"""`) process backslash escapes; literal strings
# (`'`, `'''`) do not -- a backslash there is just a character.
_TOML_STRINGS = (
    ('"""', '"""', True, True),
    ("'''", "'''", False, True),
    ('"', '"', True, False),
    ("'", "'", False, False),
)

# Kotlin raw (triple-quoted) strings do not process escapes either; Java text
# blocks do.
_KOTLIN_STRINGS = (('"""', '"""', False, True),) + _C_STRINGS
_JAVA_STRINGS = (('"""', '"""', True, True),) + _C_STRINGS

LANGS = {
    "go": Lang(("//",), (("/*", "*/", False),), _C_STRINGS + (("`", "`", False, True),)),
    # Rust is the one language here that nests block comments by specification.
    "rust": Lang(("//",), (("/*", "*/", True),), _C_STRINGS),
    "typescript": Lang(
        ("//",), (("/*", "*/", False),), _C_STRINGS + (("`", "`", True, True),)
    ),
    "c": Lang(("//",), (("/*", "*/", False),), _C_STRINGS),
    # Kotlin block comments nest by specification, like Rust's.
    "kotlin": Lang(("//",), (("/*", "*/", True),), _KOTLIN_STRINGS),
    "java": Lang(("//",), (("/*", "*/", False),), _JAVA_STRINGS),
    "python": Lang(
        ("#",), (),
        (('"""', '"""', True, True), ("'''", "'''", True, True)) + _C_STRINGS,
        docstrings=True,
    ),
    # Heredoc bodies are data passed to a command, not shell syntax.
    "shell": Lang(("#",), (), _C_STRINGS, heredocs=True),
    "yaml": Lang(("#",), (), _C_STRINGS),
    "nix": Lang(("#",), (("/*", "*/", False),), _C_STRINGS),
    "sql": Lang(("--",), (("/*", "*/", False),), (("'", "'", False, False),)),
    "lua": Lang(("--",), (("--[[", "]]", False),), _C_STRINGS),
    "html": Lang((), (("<!--", "-->", False),), _C_STRINGS),
    "toml": Lang(("#",), (), _TOML_STRINGS),
}

EXTENSIONS = {
    ".go": "go", ".rs": "rust",
    ".ts": "typescript", ".tsx": "typescript", ".js": "typescript", ".jsx": "typescript",
    ".c": "c", ".h": "c", ".cc": "c", ".cpp": "c", ".hpp": "c",
    ".java": "java", ".kt": "kotlin",
    ".py": "python", ".pyi": "python",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell",
    ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".nix": "nix",
    ".sql": "sql",
    ".lua": "lua",
    ".html": "html", ".htm": "html", ".xml": "html",
}

# Per-block token selection (`//` inside <script> versus `<!--` in the template)
# is not implemented, so these are skipped and counted rather than half-scanned
# with the HTML table, which would silently miss every script-block comment.
MULTI_LANGUAGE_SUFFIXES = {".vue", ".svelte", ".astro"}

SHEBANGS = (
    ("python", "python"), ("bash", "shell"), ("sh", "shell"), ("zsh", "shell"),
)

# Out of scope by decision, not by limitation: this repo alone has 628 tracked
# .md files whose `# Step 1:` headings and fenced examples are content.
OUT_OF_SCOPE_SUFFIXES = {".md", ".markdown", ".mdx"}


def detect_language(path):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in EXTENSIONS:
        return EXTENSIONS[suffix]
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            first = fh.readline()
    except OSError:
        return None
    if first.startswith("#!"):
        for needle, lang in SHEBANGS:
            if needle in first:
                return lang
    return None


def scan(text, lang):
    """Comment spans in `text`, as 1-indexed inclusive line ranges."""
    spans = []
    index, line, length = 0, 1, len(text)
    # Longest tokens first so `--[[` wins over `--` and `"""` over `"`.
    line_tokens = sorted(lang.line, key=len, reverse=True)
    blocks = sorted(lang.block, key=lambda pair: len(pair[0]), reverse=True)
    strings = sorted(lang.strings, key=lambda triple: len(triple[0]), reverse=True)

    while index < length:
        char = text[index]

        if char == "\n":
            line += 1
            index += 1
            continue

        if lang.heredocs and text.startswith("<<", index):
            heredoc_match = _HEREDOC_START.match(text, index)
            if heredoc_match:
                new_index = _skip_heredoc(text, index, heredoc_match)
                line += text.count("\n", index, new_index)
                index = new_index
                continue

        matched_string = next(
            (s for s in strings if text.startswith(s[0], index)), None
        )
        if matched_string:
            opener, closer, escapes, multiline = matched_string
            if not multiline:
                # A single-line literal whose closer is not on this line is not a
                # literal: it is an apostrophe in prose. Treating it as one would
                # swallow every comment in the rest of the file.
                probe = text.find(closer, index + len(opener))
                newline = text.find("\n", index + len(opener))
                if probe == -1 or (newline != -1 and newline < probe):
                    index += 1
                    continue
            # A docstring is a string literal to the parser but a comment to a
            # reader, so it is the one string we emit rather than skip.
            is_docstring = (
                lang.docstrings
                and len(opener) == 3
                and _in_docstring_position(text, index)
            )
            start_line = line
            start_index = index
            index += len(opener)
            while index < length:
                if escapes and text[index] == "\\":
                    if text[index + 1: index + 2] == "\n":
                        line += 1
                    index += 2
                    continue
                if text.startswith(closer, index):
                    index += len(closer)
                    break
                if text[index] == "\n":
                    line += 1
                index += 1
            if is_docstring:
                spans.append({
                    "start_line": start_line, "end_line": line,
                    "text": text[start_index:index], "kind": "docstring",
                })
            continue

        matched_block = next(
            (b for b in blocks if text.startswith(b[0], index)), None
        )
        if matched_block:
            opener, closer, nests = matched_block
            start_line = line
            # Walk to the matching closer by depth. Taking the first closer would
            # end a nested Rust comment early, and rewriting that span would leave
            # a dangling tail behind -- the reviewer editing live code.
            cursor, depth = index + len(opener), 1
            while cursor < length:
                if nests and text.startswith(opener, cursor):
                    depth += 1
                    cursor += len(opener)
                    continue
                if text.startswith(closer, cursor):
                    depth -= 1
                    cursor += len(closer)
                    if depth == 0:
                        break
                    continue
                cursor += 1
            end = cursor
            body = text[index:end]
            line += body.count("\n")
            spans.append({
                "start_line": start_line, "end_line": line,
                "text": body, "kind": "block",
            })
            index = end
            continue

        matched_line = next(
            (t for t in line_tokens if text.startswith(t, index)), None
        )
        if matched_line:
            end = text.find("\n", index)
            end = length if end == -1 else end
            spans.append({
                "start_line": line, "end_line": line,
                "text": text[index:end], "kind": "line",
            })
            index = end
            continue

        index += 1

    return spans


def extract(path):
    path = Path(path)
    record = {"file": str(path), "lang": None, "comments": [], "skipped": None}

    if path.suffix.lower() in OUT_OF_SCOPE_SUFFIXES:
        record["skipped"] = "markdown-out-of-scope"
        return record
    if path.suffix.lower() in MULTI_LANGUAGE_SUFFIXES:
        record["skipped"] = "multi-language-unsupported"
        return record
    try:
        raw = path.read_bytes()
    except OSError:
        record["skipped"] = "unreadable"
        return record
    if len(raw) > MAX_BYTES:
        record["skipped"] = "too-large"
        return record
    if b"\x00" in raw[:BINARY_SNIFF_BYTES]:
        record["skipped"] = "binary"
        return record

    lang = detect_language(path)
    if lang is None:
        record["skipped"] = "unknown-language"
        return record

    record["lang"] = lang
    # Decoded without universal-newline translation, so a CRLF file's comment
    # `text` keeps its trailing `\r`. That is deliberate: `text` is used to
    # locate and replace the span, so it must match the file's bytes exactly.
    record["comments"] = scan(raw.decode("utf-8", errors="replace"), LANGS[lang])
    return record


def main():
    paths = [line.strip() for line in sys.stdin.read().splitlines() if line.strip()]
    json.dump({"files": [extract(p) for p in paths]}, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
