# Global Claude Code Instructions

## Git Commits and PRs

When creating commits and pull requests:
- Do NOT add the "Generated with Claude Code" watermark line
- Do NOT add the "Co-Authored-By: Claude" line
- Keep commit messages and PR descriptions clean and professional

## Git Worktrees

When working with git worktrees, use `cd` instead of `git -C`:

```bash
# CORRECT - cd into worktree then run git commands:
cd .worktrees/feature-branch && git log --oneline
cd .worktrees/feature-branch && git status

# INCORRECT - do NOT use git -C:
git -C .worktrees/feature-branch log --oneline
```

This ensures proper permission handling. The `cd <path> && <git command>` pattern is allowed and matches existing git permission rules.
