# Herdr Agent Labels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Label every Claude agent in herdr with its PR and branch, show Claude's title in the sidebar, and add a fuzzy agent search.

**Architecture:** One stdlib Python script reads `herdr agent list` plus each session's transcript tail, reports `pr`/`branch` tokens per pane, and can also print a TSV for an fzf wrapper. chezmoi installs the scripts and a 30-minute systemd user timer; herdr `config.toml` (stow) gets the sidebar row and popup key.

**Tech Stack:** Python 3 stdlib, bash, fzf, systemd user units, chezmoi templates.

**Spec:** `docs/superpowers/specs/2026-11-25-herdr-agent-labels-design.md`

## Global Constraints

- No LLM calls; title = herdr `terminal_title_stripped`.
- Never `herdr pane rename`; only `pane report-metadata --source labels`.
- No PR link found → `--clear-token pr` (never guess).
- chezmoi targets only on hosts where `lookPath "herdr"` succeeds.
- Timer: `OnBootSec=1min`, `OnUnitActiveSec=30min`.
- Search key: `prefix+/`, popup.

## Review Focus

- Transcript missing (new session, other agent kind) → labels cleared, no crash.
- Transcript of 16 MB+ → only the tail is read; first partial line skipped.
- cwd containing `.` or `_` → project dir encoding matches Claude's (`/`, `.`, `_` → `-`).
- GitLab MR URL → `!N`; GitHub PR → `#N`; latest URL wins.
- herdr not running (timer fires before login session) → exit 0 quietly.

---

### Task 1: `herdr-agent-labels` core + tests

**Files:**
- Create: `chezmoi/dot_local/bin/executable_herdr-agent-labels`
- Test: `scripts/tests/test_herdr_agent_labels.py`

**Interfaces:**
- Produces: `project_dir(cwd: str) -> Path`, `read_tail(path: Path, limit: int = 4_000_000) -> list[dict]`, `extract(entries: list[dict]) -> tuple[str | None, str | None]` (branch, pr), CLI `herdr-agent-labels [--list]`; `--list` prints TSV `pane_id\ttitle\tpr\tbranch\tworkspace:tab\tcwd`.

- [ ] Tests: `project_dir("/home/k/git_repos/a.b_c")` ends with `-home-k-git-repos-a-b-c`; `extract` returns last `gitBranch` and last PR URL formatted `#802` / `!17`; missing data → `(None, None)`; `read_tail` on a file larger than limit skips the partial first line.
- [ ] Run `python3 -m pytest scripts/tests -q` → FAIL.
- [ ] Implement; default mode runs `herdr pane report-metadata` per Claude agent.
- [ ] Tests PASS; run once live, check `herdr pane get` / sidebar.

### Task 2: search popup, sidebar, timer, chezmoi gating

**Files:**
- Create: `chezmoi/dot_local/bin/executable_herdr-agent-search`
- Create: `chezmoi/dot_config/systemd/user/herdr-agent-labels.{service,timer}`
- Create: `chezmoi/run_onchange_after_enable-herdr-agent-labels.sh.tmpl`
- Modify: `chezmoi/.chezmoiignore`, `.config/herdr/config.toml`

- [ ] `herdr-agent-search`: `herdr-agent-labels --list | fzf` → `herdr agent focus <pane>`.
- [ ] config.toml: `rows_by_agent.claude` and `[[keys.command]] key="prefix+/"`; `herdr server reload-config` clean.
- [ ] `chezmoi -S <worktree> diff` / `apply`; `systemctl --user list-timers` shows the timer.
- [ ] Commit, push.
