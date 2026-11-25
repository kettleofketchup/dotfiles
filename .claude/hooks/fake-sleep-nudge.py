#!/usr/bin/env python3
"""PreToolUse hook: refuse `read ... < /dev/zero` (and friends) used as a sleep.

The harness blocks a foreground `sleep`, so agents that want to poll reach for
`read -t 10 < /dev/zero` as a substitute. It does not wait: `-t` only bounds the
wait for input, and /dev/zero always has input. `read` instead slurps NUL bytes
at full CPU into a line that never ends. In zsh 5.9 the buffer size is an int,
so after ~1 GiB of NULs it overflows and the shell segfaults in bin_read
(observed 2026-11-25, PID 2672715). /dev/urandom behaves the same way, just
slower.

The real fix is not a better sleep but no polling at all: run the long job with
run_in_background and wait for the completion notification, or use Monitor
with an until-loop.

Escape hatch: put `# allow-devzero-read` anywhere in the command.

Wiring (user-global, in dotfiles): a `PreToolUse` hook with matcher `Bash`.
"""

import json
import re
import sys

# `read` as a command word (line start or after ; & | ( or `||`/`&&`), then a
# redirect from /dev/zero or /dev/urandom/random somewhere on the same simple
# command (no ; & | in between). Covers `<`, `<>`, and `0<`.
PATTERN = re.compile(
    r"(?:^|[;&|(]|\bthen|\bdo|\belse)\s*(?:builtin\s+)?read\b[^;&|\n]*"
    r"\d*<>?\s*/dev/(?:zero|u?random)\b"
)

OPT_OUT = "# allow-devzero-read"

REASON = (
    "`read ... < /dev/zero` is not a sleep. `-t` only limits the wait for "
    "input, and /dev/zero never runs dry, so `read` spins at 100% CPU slurping "
    "NUL bytes into an endless line. zsh segfaults once that buffer passes "
    "~2 GiB (this crashed a shell on 2026-11-25).\n\n"
    "Don't poll with a sleep substitute. Instead:\n"
    "  - Start the long job with run_in_background: true and wait for the "
    "completion notification, or\n"
    "  - Use the Monitor tool with an until-loop for a condition you can't "
    "otherwise be notified about.\n\n"
    "If you truly need this redirect for something other than sleeping, add "
    "`# allow-devzero-read` to the command."
)


def blocked(command: str) -> bool:
    return OPT_OUT not in command and bool(PATTERN.search(command))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # Never block on a malformed payload.

    if payload.get("tool_name") != "Bash":
        return 0

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not blocked(command):
        return 0

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": REASON,
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        should_block = [
            # The exact command that crashed zsh.
            'for i in $(seq 1 57); do grep -q "^EXIT=" $L && break; '
            'read -t 10 < /dev/zero 2>/dev/null || python3 -c "import time"; done',
            "read -t 10 < /dev/zero",
            "read -t5 </dev/zero",
            "read -t 10 <> /dev/zero",
            "builtin read -t 3 < /dev/urandom",
            "true && read -r x 0< /dev/zero",
            "while true; do read -t 1 < /dev/random; done",
        ]
        should_allow = [
            "head -c 1M /dev/zero > file.bin",
            "dd if=/dev/zero of=img bs=1M count=10",
            "while read -r line; do echo $line; done < input.txt",
            "read -r name < /etc/hostname",
            "grep -n 'read -t 10 < /dev/zero' notes.md",
            "echo x | read y; cat /dev/zero | head -c 4",
            "read -t 10 < /dev/zero  # allow-devzero-read",
            "thread_count=4 < /dev/zero",
        ]
        ok = True
        for c in should_block:
            hit = blocked(c)
            print(("PASS " if hit else "FAIL ") + "block  " + c)
            ok &= hit
        for c in should_allow:
            hit = blocked(c)
            print(("PASS " if not hit else "FAIL ") + "allow  " + c)
            ok &= not hit
        sys.exit(0 if ok else 1)
    sys.exit(main())
