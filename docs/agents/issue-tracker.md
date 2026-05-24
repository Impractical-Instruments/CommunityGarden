# Issue tracker: GitHub

Issues and PRDs for this repo live as GitHub Issues (`Impractical-Instruments/CommunityGarden`). Use the `gh` CLI via Bash for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..." --label "..."`
- **Read an issue**: `gh issue view <number>` (add `--json title,body,labels,state` for parseable output)
- **List issues**: `gh issue list --state open --label needs-triage`
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

Pass multi-line bodies via a heredoc to preserve formatting (see the global instructions for the `gh pr create` example).

## When a skill says "publish to the issue tracker"

Run `gh issue create` from Bash.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number>`.
