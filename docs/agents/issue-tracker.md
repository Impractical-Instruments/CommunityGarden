# Issue tracker: GitHub

Issues and PRDs for this repo live as GitHub Issues (`Impractical-Instruments/CommunityGarden`). Use the GitHub MCP tools (`mcp__github__*`) for all operations.

## Conventions

- **Create an issue**: `mcp__github__issue_write` with `owner`, `repo`, `title`, `body`.
- **Read an issue**: `mcp__github__issue_read` with `issue_number`.
- **List issues**: `mcp__github__list_issues` filtered by `state`, `labels`.
- **Comment on an issue**: `mcp__github__add_issue_comment`.
- **Apply / remove labels**: `mcp__github__issue_write` with updated `labels`.
- **Close**: `mcp__github__issue_write` with `state: "closed"` and a closing comment via `mcp__github__add_issue_comment`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue via `mcp__github__issue_write`.

## When a skill says "fetch the relevant ticket"

Call `mcp__github__issue_read` with the issue number.
