#!/usr/bin/env python3
"""
Bash command formatter hook for Claude Code.

Enforces proper tool usage by:
1. Blocking file write patterns that should use the Write tool instead
2. Blocking file read patterns that should use the Read tool instead
3. Blocking search patterns that should use Grep/Glob tools instead
4. Blocking edit patterns that should use the Edit tool instead
5. Blocking multi-command bash lines - run separately for proper permissions
"""

import json
import sys
import re


# =============================================================================
# REGEX PATTERNS
# =============================================================================

# Multi-command patterns (split on these)
MULTI_COMMAND_PATTERN = re.compile(r'\s*(?:&&|\|\||;)\s*')

# File write patterns - should use Write tool
# These patterns look for actual file redirects, not > inside quoted strings
FILE_WRITE_PATTERNS = [
    # echo to file: echo "text" > file or echo 'text' > file or echo text > file
    # Must end with > or >> followed by filename (not inside quotes)
    (re.compile(r'^echo\s+.+\s+>{1,2}\s*\S+\s*$'),
     "echo redirect",
     "Use the Write tool to create/overwrite files",
     "Write"),

    # printf to file: printf "format" args > file
    (re.compile(r'^printf\s+.+\s+>{1,2}\s*\S+\s*$'),
     "printf redirect",
     "Use the Write tool to create/overwrite files",
     "Write"),

    # Heredoc patterns: cat << EOF > file, cat <<'EOF' > file, cat <<-EOF > file
    (re.compile(r'^cat\s*<<-?\s*[\'"]?\w+[\'"]?'),
     "heredoc (cat << EOF)",
     "Use the Write tool to create/overwrite files",
     "Write"),

    # tee for file creation: echo x | tee file or tee file <<< "text"
    (re.compile(r'\|\s*tee\s+[^|]+$'),
     "pipe to tee",
     "Use the Write tool to create/overwrite files",
     "Write"),

    (re.compile(r'^tee\s+\S+\s*<<<'),
     "tee with herestring",
     "Use the Write tool to create/overwrite files",
     "Write"),

    # cat > file (creating new file interactively or with redirect)
    (re.compile(r'^cat\s*>{1,2}\s*\S+'),
     "cat redirect",
     "Use the Write tool to create/overwrite files",
     "Write"),
]

# File read patterns - should use Read tool
FILE_READ_PATTERNS = [
    # cat file (but not cat << or cat > or cat |)
    (re.compile(r'^cat\s+(?!<<|>)[^|><]+$'),
     "cat <file>",
     "Use the Read tool to read file contents",
     "Read"),

    # head command
    (re.compile(r'^head\s+'),
     "head",
     "Use the Read tool with limit parameter",
     "Read"),

    # tail command
    (re.compile(r'^tail\s+'),
     "tail",
     "Use the Read tool with offset parameter",
     "Read"),
]

# Search patterns - should use Grep/Glob tools
SEARCH_PATTERNS = [
    # grep command
    (re.compile(r'^grep\s+'),
     "grep",
     "Use the Grep tool for content searching",
     "Grep"),

    # ripgrep command
    (re.compile(r'^rg\s+'),
     "rg (ripgrep)",
     "Use the Grep tool for content searching",
     "Grep"),

    # find with -name (file searching)
    (re.compile(r'^find\s+.*-name\s+'),
     "find -name",
     "Use the Glob tool for finding files by pattern",
     "Glob"),

    # find with -type (file searching)
    (re.compile(r'^find\s+.*-type\s+'),
     "find -type",
     "Use the Glob tool for finding files",
     "Glob"),
]

# Edit patterns - should use Edit tool
EDIT_PATTERNS = [
    # sed -i (in-place edit)
    (re.compile(r'^sed\s+.*-i'),
     "sed -i",
     "Use the Edit tool for in-place file modifications",
     "Edit"),

    # sed with -i flag anywhere
    (re.compile(r'^sed\s+-i'),
     "sed -i",
     "Use the Edit tool for in-place file modifications",
     "Edit"),

    # awk with inplace
    (re.compile(r'^awk\s+.*-i\s*inplace'),
     "awk -i inplace",
     "Use the Edit tool for in-place file modifications",
     "Edit"),
]


# Pattern to match leading cd command (cd <path> &&)
# Handles: cd /path && ..., cd "/path with spaces" && ..., cd '/path' && ...
CD_PREFIX_PATTERN = re.compile(r'^cd\s+(?:"[^"]*"|\'[^\']*\'|\S+)\s*&&\s*')


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def strip_cd_prefix(command: str) -> str:
    """Strip leading 'cd <path> &&' from a command for multi-command checking."""
    return CD_PREFIX_PATTERN.sub('', command.strip())


def split_commands(command: str) -> list[str]:
    """Split a bash command into individual commands."""
    commands = []

    # First, split on newlines
    lines = command.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Skip line continuations (ending with \)
        line = re.sub(r'\s*\\$', '', line)

        # Split on && and || and ; (simple approach, doesn't handle quotes)
        parts = MULTI_COMMAND_PATTERN.split(line)

        for part in parts:
            part = part.strip()
            if part:
                commands.append(part)

    return commands


def check_patterns(command: str, patterns: list) -> tuple[str, str, str] | None:
    """Check command against a list of patterns.

    Returns (pattern_name, suggestion, tool_name) or None if no match.
    """
    for pattern, name, suggestion, tool in patterns:
        if pattern.search(command):
            return (name, suggestion, tool)
    return None


# =============================================================================
# MAIN
# =============================================================================

def main():
    # Debug logging
    log_path = "/tmp/bash-hook-debug.log"
    with open(log_path, "a") as f:
        f.write(f"\n--- Hook invoked ---\n")

    try:
        raw_input = sys.stdin.read()
        with open(log_path, "a") as f:
            f.write(f"Raw input: {raw_input}\n")
        input_data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        with open(log_path, "a") as f:
            f.write(f"JSON decode error: {e}\n")
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    description = tool_input.get("description", "")

    if not command:
        sys.exit(0)

    # Log the command being checked
    with open(log_path, "a") as f:
        f.write(f"Checking command: {command}\n")

    # -------------------------------------------------------------------------
    # Check 1: File write patterns (echo > file, heredoc, tee, etc.)
    # -------------------------------------------------------------------------
    match = check_patterns(command, FILE_WRITE_PATTERNS)
    if match:
        pattern_name, suggestion, correct_tool = match
        lines = [
            "=" * 60,
            "BLOCKED: File write pattern detected",
            "=" * 60,
            "",
            f"Pattern:  {pattern_name}",
            f"Command:  {command[:200]}{'...' if len(command) > 200 else ''}",
            "",
            f"Problem:  Using Bash to write files bypasses permission controls",
            f"Solution: {suggestion}",
            "",
            f"The {correct_tool} tool is the correct way to perform this operation.",
            "It provides proper permission management and change tracking.",
        ]
        print('\n'.join(lines), file=sys.stderr)
        sys.exit(2)

    # -------------------------------------------------------------------------
    # Check 2: File read patterns (cat, head, tail)
    # -------------------------------------------------------------------------
    match = check_patterns(command, FILE_READ_PATTERNS)
    if match:
        pattern_name, suggestion, correct_tool = match
        lines = [
            "=" * 60,
            "BLOCKED: File read pattern detected",
            "=" * 60,
            "",
            f"Pattern:  {pattern_name}",
            f"Command:  {command}",
            "",
            f"Solution: {suggestion}",
            "",
            f"The {correct_tool} tool is optimized for reading files and supports",
            "offset/limit parameters for large files.",
        ]
        print('\n'.join(lines), file=sys.stderr)
        sys.exit(2)

    # -------------------------------------------------------------------------
    # Check 3: Search patterns (grep, rg, find)
    # -------------------------------------------------------------------------
    match = check_patterns(command, SEARCH_PATTERNS)
    if match:
        pattern_name, suggestion, correct_tool = match
        lines = [
            "=" * 60,
            "BLOCKED: Search pattern detected",
            "=" * 60,
            "",
            f"Pattern:  {pattern_name}",
            f"Command:  {command}",
            "",
            f"Solution: {suggestion}",
            "",
            f"The {correct_tool} tool is optimized for searching and provides",
            "better integration with Claude Code.",
        ]
        print('\n'.join(lines), file=sys.stderr)
        sys.exit(2)

    # -------------------------------------------------------------------------
    # Check 4: Edit patterns (sed -i, awk inplace)
    # -------------------------------------------------------------------------
    match = check_patterns(command, EDIT_PATTERNS)
    if match:
        pattern_name, suggestion, correct_tool = match
        lines = [
            "=" * 60,
            "BLOCKED: In-place edit pattern detected",
            "=" * 60,
            "",
            f"Pattern:  {pattern_name}",
            f"Command:  {command}",
            "",
            f"Solution: {suggestion}",
            "",
            f"The {correct_tool} tool provides proper change tracking and",
            "permission management for file modifications.",
        ]
        print('\n'.join(lines), file=sys.stderr)
        sys.exit(2)

    # -------------------------------------------------------------------------
    # Check 5: Multi-command patterns (&&, ||, ;, newlines)
    # Allow "cd <path> && <single command>" pattern
    # -------------------------------------------------------------------------
    command_without_cd = strip_cd_prefix(command)
    commands = split_commands(command_without_cd)

    if len(commands) > 1:
        lines = [
            "=" * 60,
            "BLOCKED: Multiple commands detected",
            "=" * 60,
            "",
            "This command contains multiple chained commands that should be",
            "run separately for proper permission management.",
            "",
            "Commands to run individually:",
            "",
        ]

        for i, cmd in enumerate(commands, 1):
            lines.append(f"  {i}. {cmd}")

        lines.extend([
            "",
            "Why this matters:",
            "  - Each command can be individually added to the permission allow list",
            "  - Failures are easier to identify and debug",
            "  - Permission prompts are clearer for each operation",
        ])

        print('\n'.join(lines), file=sys.stderr)
        sys.exit(2)

    # All checks passed - allow the command
    with open(log_path, "a") as f:
        f.write(f"ALLOWED: {command}\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
