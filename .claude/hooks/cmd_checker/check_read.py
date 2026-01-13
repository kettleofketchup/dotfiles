#!/usr/bin/env python3
"""Check for file read patterns that should use the Read tool."""

import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import check_patterns, block_command

# File read patterns - should use Read tool
FILE_READ_PATTERNS = [
    (re.compile(r'^cat\s+(?!<<|>)[^|><]+$'),
     "cat <file>",
     "Use the Read tool to read file contents",
     "Read"),

    (re.compile(r'^head\s+'),
     "head",
     "Use the Read tool with limit parameter",
     "Read"),

    (re.compile(r'^tail\s+'),
     "tail",
     "Use the Read tool with offset parameter",
     "Read"),
]


def check(command: str) -> None:
    """Check command and block if it matches read patterns."""
    match = check_patterns(command, FILE_READ_PATTERNS)
    if match:
        pattern_name, suggestion, correct_tool = match
        block_command(
            title="File read pattern detected",
            pattern_name=pattern_name,
            command=command,
            problem="Using Bash for file reading is less efficient",
            solution=suggestion,
            tool_name=correct_tool,
            extra_lines=[
                "It is optimized for reading files and supports",
                "offset/limit parameters for large files."
            ]
        )


if __name__ == "__main__":
    try:
        data = json.loads(sys.stdin.read())
        command = data.get("tool_input", {}).get("command", "")
        if command:
            check(command)
    except SystemExit:
        raise
    except Exception:
        pass
    sys.exit(0)
