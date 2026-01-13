# Claude Code Bash Hooks

Modular command checker that validates Bash commands before execution in Claude Code.

## Structure

```
hooks/
├── cmd_checker/              # Main hook module (runs checks in parallel)
│   ├── __main__.py           # Entry point - orchestrates parallel checks
│   ├── common.py             # Shared utilities
│   ├── check_write.py        # Blocks file write patterns
│   ├── check_read.py         # Blocks file read patterns
│   ├── check_search.py       # Blocks search patterns (with exceptions)
│   ├── check_edit.py         # Blocks in-place edit patterns
│   └── check_multi_command.py # Blocks command chains (with exceptions)
├── bash-format.py            # Legacy monolithic hook (deprecated)
└── README.md                 # This file
```

## How It Works

1. **Single hook call** in settings.json invokes `cmd_checker`
2. `cmd_checker/__main__.py` runs all check modules **in parallel** using ThreadPoolExecutor
3. Each module returns exit 0 (allow) or exit 2 (block)
4. If any module blocks, the command is blocked immediately

## settings.json Configuration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -m cmd_checker",
            "workingDirectory": "/home/kettle/.claude/hooks",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Exceptions Built In

### check_search.py
- **Single grep/rg commands**: Allowed for quick context gathering
- **grep -c or grep | wc**: Counting matches allowed
- **grep | head/tail**: Getting subsets allowed

### check_multi_command.py
- **cd <path> && <command>**: Directory context allowed
- **Commands ending with echo**: Showing results allowed

## Updating Hooks

### Add a New Pattern

Edit the appropriate `cmd_checker/check_*.py` file:

```python
# In check_write.py for example
FILE_WRITE_PATTERNS = [
    # ... existing patterns ...

    (re.compile(r'^your_pattern'),
     "pattern name",
     "Use the X tool instead",
     "ToolName"),
]
```

### Add a New Exception

**For search** - Edit `cmd_checker/check_search.py`:
```python
EXCEPTION_PATTERNS = [
    # ... existing ...
    re.compile(r'^your_exception'),
]
```

**For multi-command** - Edit `cmd_checker/check_multi_command.py`:
```python
def is_exception(command: str, commands: list[str]) -> bool:
    # Add your logic
    if your_condition:
        return True
```

### Create a New Check Module

1. Create `cmd_checker/check_yourname.py`:
```python
#!/usr/bin/env python3
"""Description of what this checks."""

import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import check_patterns, block_command

YOUR_PATTERNS = [
    (re.compile(r'^pattern'), "name", "suggestion", "Tool"),
]

def check(command: str) -> None:
    """Check and block if matches."""
    match = check_patterns(command, YOUR_PATTERNS)
    if match:
        pattern_name, suggestion, tool = match
        block_command(
            title="Your title",
            pattern_name=pattern_name,
            command=command,
            problem="Why blocked",
            solution=suggestion,
            tool_name=tool
        )

if __name__ == "__main__":
    try:
        data = json.loads(sys.stdin.read())
        command = data.get("tool_input", {}).get("command", "")
        if command:
            check(command)
    except:
        pass
    sys.exit(0)
```

2. Add to `cmd_checker/__main__.py`:
```python
CHECK_MODULES = [
    # ... existing ...
    "check_yourname.py",
]
```

### Disable a Check Module

Remove or comment out in `cmd_checker/__main__.py`:
```python
CHECK_MODULES = [
    "check_write.py",
    "check_read.py",
    # "check_search.py",  # Disabled
    "check_edit.py",
    "check_multi_command.py",
]
```

## Debugging

All hooks log to `/tmp/bash-hook-debug.log`:

```bash
tail -f /tmp/bash-hook-debug.log
```

## Blocked Patterns Reference

### check_write.py
| Pattern | Example | Use Instead |
|---------|---------|-------------|
| echo redirect | `echo "x" > file` | Write tool |
| printf redirect | `printf "x" > file` | Write tool |
| heredoc | `cat << EOF` | Write tool |
| tee | `echo x \| tee file` | Write tool |
| cat redirect | `cat > file` | Write tool |

### check_read.py
| Pattern | Example | Use Instead |
|---------|---------|-------------|
| cat file | `cat README.md` | Read tool |
| head | `head -n 50 file` | Read tool |
| tail | `tail -n 20 file` | Read tool |

### check_search.py
| Pattern | Example | Use Instead |
|---------|---------|-------------|
| grep | `grep "x" file` | Grep tool |
| rg | `rg "x" src/` | Grep tool |
| find -name | `find . -name "*.py"` | Glob tool |
| find -type | `find . -type f` | Glob tool |

**Note:** Single grep/rg commands ARE allowed as exceptions.

### check_edit.py
| Pattern | Example | Use Instead |
|---------|---------|-------------|
| sed -i | `sed -i 's/a/b/' file` | Edit tool |
| awk inplace | `awk -i inplace '...'` | Edit tool |

### check_multi_command.py
| Pattern | Example |
|---------|---------|
| && chain | `cmd1 && cmd2` |
| \|\| chain | `cmd1 \|\| cmd2` |
| ; chain | `cmd1; cmd2` |

**Exceptions:** `cd path && cmd` and `cmd && echo` allowed.

## Exit Codes

- `0` - Allow the command
- `2` - Block the command (with message to stderr)
