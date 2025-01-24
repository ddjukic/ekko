---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git diff:*), Bash(git rev-parse:*)
argument-hint: [type(target): description]
description: Create a git commit FOR EACH MODIFIED FILED SEPARATELY with enforced conventional message format: type(target): description
---

## Commit message rules

- Use: `type(target): description`
- Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `perf`, `test`, `style`, `build`, `ci`
- Target: the main file, component, or area (e.g., `learning-path`, `project-workspace`)
- Description: imperative, concise, no trailing period

Examples:
- `feat(project-workspace): add Curriculum/Lesson toggle and markmap rendering`
- `fix(learning-path): center sidebar and avoid chevron overlap`

## Context

- Current branch: !`git rev-parse --abbrev-ref HEAD`
- Status: !`git status -s`
- Diff (staged): !`git diff --cached --stat`

## Your task

1) Validate the provided commit message argument strictly matches the format.
2) If valid, run: `git commit -m "<message>"`.
3) If not valid, respond with the required format and examples; do not commit.

Usage:

```
/commit feat(project-workspace): scope scrolling to lesson body and add frame
```

Reference: [Claude Code slash commands](https://docs.anthropic.com/en/docs/claude-code/slash-commands)
