#!/usr/bin/env python3
"""Check for file write patterns that should use the Write tool."""

import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import check_patterns, block_command

# File write patterns - should use Write tool
FILE_WRITE_PATTERNS = [
    (re.compile(r'^echo\s+.+\s+>{1,2}\s*\S+\s*$'),
     "echo redirect",
     "Use the Write tool to create/overwrite files",
     "Write"),

    (re.compile(r'^printf\s+.+\s+>{1,2}\s*\S+\s*$'),
     "printf redirect",
     "Use the Write tool to create/overwrite files",
     "Write"),

    (re.compile(r'^cat\s*<<-?\s*[\'"]?\w+[\'"]?'),
     "heredoc (cat << EOF)",
     "Use the Write tool to create/overwrite files",
     "Write"),

    (re.compile(r'\|\s*tee\s+[^|]+$'),
     "pipe to tee",
     "Use the Write tool to create/overwrite files",
     "Write"),

    (re.compile(r'^tee\s+\S+\s*<<<'),
     "tee with herestring",
     "Use the Write tool to create/overwrite files",
     "Write"),

    (re.compile(r'^cat\s*>{1,2}\s*\S+'),
     "cat redirect",
     "Use the Write tool to create/overwrite files",
     "Write"),
]


def check(command: str) -> None:
    """Check command and block if it matches write patterns."""
    match = check_patterns(command, FILE_WRITE_PATTERNS)
    if match:
        pattern_name, suggestion, correct_tool = match
        block_command(
            title="File write pattern detected",
            pattern_name=pattern_name,
            command=command,
            problem="Using Bash to write files bypasses permission controls",
            solution=suggestion,
            tool_name=correct_tool,
            extra_lines=["It provides proper permission management and change tracking."]
        )


if __name__ == "__main__":
    try:
        data = json.loads(sys.stdin.read())
        command = data.get("tool_input", {}).get("command", "")
        if command:
            check(command)
    except SystemExit:
        raise  # Re-raise sys.exit()
    except Exception:
        pass
    sys.exit(0)
