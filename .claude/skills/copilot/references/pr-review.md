# Copilot code review — setup, request, behavior

## Plan requirements

| Plan | Code review available? |
|------|-----------------------|
| Copilot Free | No |
| Copilot Pro | Yes |
| Copilot Pro+ | Yes |
| Copilot Business | Yes (org policy must allow it) |
| Copilot Enterprise | Yes (org policy must allow it) |

Org admins additionally need two policies enabled to let unlicensed org members use review: **"Premium request paid usage"** and **"Allow members without a Copilot license to use Copilot code review in GitHub.com."**

## Manual review — how to request

### CLI (`gh`)

```bash
# At PR creation
gh pr create --reviewer @copilot

# On an existing PR
gh pr edit <PR-NUMBER> --add-reviewer @copilot
```

### GitHub Web UI

PR page → right sidebar → **Reviewers** menu → tick **Copilot**. Review lands in under 30 seconds.

### IDE entry points

- **VS Code:** Source Control view → "Review changes with Copilot", or select code and right-click → **Generate Code → Review**.
- **Visual Studio 17.14+:** Git Changes window → **Review changes with Copilot**.
- **JetBrains IDEs:** Commit tool window → **Copilot: Review Code Changes**.

## Automatic review — setup

### Personal (per-user, Pro / Pro+ only)

Profile picture → **Copilot settings** → **Automatic Copilot code review** → **Enabled**. Reviews fire on PRs the user opens against repos that allow it.

### Repository (via Rulesets)

`Settings → Rules → Rulesets → New branch ruleset` and configure:

1. Name the ruleset; set **Enforcement Status** = **Active**.
2. **Target branches**: add target (typically `main` or release branches).
3. **Branch rules**: tick **Automatically request Copilot code review**.
4. Optional: **Review new pushes** (re-review on every push), **Review draft pull requests** (review while still draft).
5. Click **Create**.

This is now an **independent** rule (since the Sept 2025 changelog) — no longer nested under "Require a pull request before merging".

### Organization

`Org Settings → Code, planning, and automation → Repository → Rulesets → New branch ruleset` then add target repositories (inclusion/exclusion patterns) and the same branch rule + sub-settings as the repo scope above.

## Review behavior (what to expect)

| Aspect | Behavior |
|--------|----------|
| Review type | Always posts a **Comment** review — never Approve / Request changes |
| Required-approval impact | Does not count toward required approvals; does not block merge |
| Re-review on push | **Not automatic.** Click the refresh icon next to Copilot in the Reviewers list |
| Dismissing comments | Standard PR mechanisms (Resolve, Discard, thumbs-down feedback) |
| Repeats | Copilot may re-post comments you previously dismissed when re-reviewing |
| Base branch | PR review reads custom instructions from the **PR's base branch**, not head |

## Files Copilot does NOT review

- `package.json`, lockfiles (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Gemfile.lock`, `poetry.lock`, etc.)
- Log files (`.log`)
- SVG files (`.svg`)

Other languages and file types are all in scope.

## Cost (June 1, 2026)

Copilot code review runs will consume GitHub Actions minutes starting June 1, 2026. Practical implications when proposing setups:

- **Personal / single-repo manual review:** negligible cost, fine to recommend.
- **Repo ruleset with "Review new pushes" enabled:** every push fires a run — recommend leaving this OFF unless the project has thoughtful push hygiene (squashed dev branches, etc.).
- **Org-wide ruleset:** quantify the blast radius (repos × monthly PR count × pushes per PR) before recommending.

## Quick decision tree

- **"How do I get Copilot to review THIS PR?"** → `gh pr edit <N> --add-reviewer @copilot`.
- **"How do I get Copilot to review EVERY PR on this repo?"** → repo Ruleset, leave "Review new pushes" off.
- **"How do I get Copilot to give me a re-review after my latest commit?"** → click the refresh icon in the Reviewers list.
- **"Copilot ignored my style rule"** → check that `.github/copilot-instructions.md` is on the PR's **base branch** and not nested under `.github/instructions/`.
