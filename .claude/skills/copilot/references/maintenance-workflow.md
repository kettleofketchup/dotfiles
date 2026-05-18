# Keeping Copilot config in lockstep with `.claude/skills/`

## Update order (always)

1. **Update the Claude skill first.** It's canonical.
2. **Find the matching Copilot file(s)** by searching for the pointer line:
   ```bash
   grep -rn ".claude/skills/<name>" .github/
   ```
3. **Update the Copilot summary** to match the new rule. Keep it short — the goal is "PR review catches drift," not "Copilot has full context."
4. **If the rule's scope changed** (e.g., a backend-only rule now also applies to a worker), update `applyTo:` globs.
5. **Commit the Claude skill change and the Copilot change together** so the base-branch instructions Copilot loads stay coherent.

## Per-file maintenance checklist

When editing `.github/copilot-instructions.md` or any `.github/instructions/*.instructions.md`:

- [ ] Each canonical-source pointer (`Canonical source: .claude/skills/<name>/SKILL.md`) still resolves — the referenced file exists.
- [ ] Summary is **≤10 bullets** and **≤2 pages rendered**.
- [ ] No bullet contradicts the canonical skill. If it does, fix the bullet (not the skill — unless the user explicitly decided to change the convention).
- [ ] If a `.instructions.md` file, `applyTo:` glob still matches the intended paths.
- [ ] No frontmatter typos (`applyTo:` not `apply_to:`; `excludeAgent:` not `exclude_agent:`).
- [ ] If a `.instructions.md` file is meant to be skipped during code review, `excludeAgent: "code-review"` is present.

## Drift-detection patterns

Run these periodically (or in a CI job) to surface drift:

### 1. Find skill pointers in Copilot files

```bash
grep -rn "\.claude/skills/" .github/ | sort -u
```

Then for each pointer, verify the target exists:

```bash
grep -rho "\.claude/skills/[a-z0-9-]\+/SKILL\.md" .github/ \
  | sort -u \
  | while read p; do test -f "$p" || echo "MISSING: $p"; done
```

### 2. Find Claude skills with NO Copilot mirror

```bash
ls .claude/skills/ \
  | while read s; do
      grep -rq "\.claude/skills/$s" .github/ \
        || echo "NO COPILOT MIRROR: .claude/skills/$s/"
    done
```

Not every skill needs a Copilot mirror — only ones with file-scoped rules that Copilot review can catch. Flag absences to the user; they decide if a mirror is warranted.

### 3. Length-budget check

```bash
wc -l .github/copilot-instructions.md .github/instructions/*.md 2>/dev/null \
  | awk '$1 > 80 && $2 != "total" { print }'
```

Anything over ~80 lines is probably duplicating content from a Claude skill — review and trim.

## Common gotchas

### `.github/instructions/copilot-instructions.md` is silently ignored

The repo-wide instructions MUST live at `.github/copilot-instructions.md` exactly. If a project has it nested under `.github/instructions/`, Copilot treats it as a (likely-malformed) path-scoped file and does not apply it repo-wide. Fix:

```bash
git mv .github/instructions/copilot-instructions.md .github/copilot-instructions.md
```

### Stale rules that contradict the skill

If the Copilot file says "use Poetry" but the canonical skill / repo has moved to `uv` or `just`, the Copilot rule WILL show up in PR review comments. Update on the same PR that switches the underlying tool.

### Base-branch instructions

PR review uses instructions from the PR's **base branch**, not the head. If a user adds a new rule to `.github/copilot-instructions.md` on a feature branch and immediately opens a PR, the review on THAT PR won't see the new rule — it'll see whatever is on `main`. The new rule applies to *future* PRs that branch from the updated `main`.

### `applyTo` glob mismatches

If `applyTo: "backend/**/*.py"` is set on a file but the rule references Django settings that only live in `backend/app/settings/`, Copilot will apply the rule to e.g. `backend/scripts/foo.py` where the rule makes no sense. Either tighten the glob or rewrite the rule to be more general.

## When to retire a Copilot file

Delete `.github/instructions/<name>.instructions.md` if:

- The corresponding Claude skill was removed.
- The rules it contains are now caught by linters / type-checkers / pre-commit hooks (no need to burn Copilot context on them).
- The file has been empty-ish (≤2 bullets) for multiple releases — fold those bullets into `.github/copilot-instructions.md` instead.
