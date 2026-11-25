# Herdr agent labels and search

## Intent

Dozens of Claude sessions run in herdr, many in the same checkout. Panes say
only `claude`, so finding "the session handling PR #802" means clicking
through panes. Each agent should show its PR, branch and task, and a search
should jump straight to it.

## Goals

- Sidebar row per Claude agent: task title, PR, branch.
- A herdr keybinding opens a fuzzy search over all agents (workspace, tab,
  title, PR, branch, cwd); Enter focuses the chosen agent.
- PR and branch refresh every 30 minutes, plus once at login.
- Installed by `chezmoi apply` on machines that have herdr.

## Non-goals / anti-goals

- No LLM calls. The task summary is Claude Code's own terminal title, which
  herdr already exposes as `terminal_title_stripped`.
- Never rename panes (manual names stay the user's); only report metadata.
- Never guess: a session with no PR link shows no PR rather than a wrong one.

## Approaches

- **A. Local 30-minute job (chosen).** Reads herdr's agent list and each
  session's transcript; free, covers idle sessions.
- B. A plus a Haiku-written summary: duplicates the title, costs tokens.
- C. Claude Code Stop hooks: misses idle sessions, adds per-turn work.

## Design

- **Data source.** `herdr agent list` gives `pane_id`, `agent_session.value`
  (Claude session id) and `foreground_cwd`. The transcript is
  `~/.claude/projects/<cwd with / and . → ->/<session-id>.jsonl`.
  - branch = last `gitBranch` in the transcript (per session, not per cwd).
  - PR = last GitHub `…/pull/N` or GitLab `…/-/merge_requests/N` URL in the
    transcript, rendered `#N` (GitHub) or `!N` (GitLab).
  - Read only the transcript tail (a few MB) — transcripts reach 16 MB+.
- **Reporting.** `herdr pane report-metadata <pane> --source labels
  --token pr=… --token branch=…` (`--clear-token` when nothing found).
- **`herdr-agent-labels`** — Python 3 stdlib script, the job above.
- **`herdr-agent-search`** — lists agents (title, PR, branch, workspace/tab,
  cwd) into fzf; Enter runs `herdr agent focus <pane>`.
- **Sidebar.** `[ui.sidebar.agents.rows_by_agent] claude =
  [["state_icon","workspace","tab"], ["terminal_title_stripped"],
  ["$pr","$branch"]]` in herdr `config.toml`.
- **Keybinding.** `[[keys.command]] key="prefix+/" type="popup"
  command="herdr-agent-search"`.
- **Timer.** systemd user `herdr-agent-labels.timer`, `OnBootSec=1min`,
  `OnUnitActiveSec=30min`.

## Ownership

- chezmoi: both scripts (`~/.local/bin/`), the service and timer, gated on
  `lookPath "herdr"` via `.chezmoiignore`; a `run_onchange_` script enables
  the timer.
- stow: herdr `config.toml` stays stow-owned (same on every machine); only
  the sidebar row and keybinding are added to it.

## Left to the builder

- How much transcript tail to read; fzf preview layout; script tests.
