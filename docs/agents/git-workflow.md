# Git Workflow

- **Private show content:** `ShowControl/FundingCAPTCHA/images/private/` is a clone of a separate private repo and must never be staged, committed, or referenced by name in this one — see `docs/FundingCAPTCHA.md`. Install the guard hook once per clone with `bash scripts/install-git-hooks.sh`.
## Branches

**`dev` is the integration branch and the default; `main` is what the show machines run.** See [ADR-0027](../adr/0027-dev-integrates-main-is-promoted.md).

- **Branch off `dev` and open every PR against `dev`.** Its ruleset requires a PR, squash merge, linear history and the `test` check from `tests.yml`. Nobody commits to `dev` directly.
- **Feature branches:** descriptive names, typically prefixed with the author or tool (e.g. `claude/update-osc-schema-xY3kQ`).
- **Open the PR with `gh pr create`**, summarising the work and naming the issues it closes. With `dev` as the default branch, `gh` targets it without `--base`.
- **`main` moves only by promotion.** Actions → *Promote dev to main* → Run workflow ([`promote.yml`](../../.github/workflows/promote.yml)) fast-forwards `main` to `dev`. No PR targets `main`, and its ruleset blocks every push except the promotion App's. A show machine that updates with `git pull` gets the last promoted `dev`.
- **Once per clone**, point `origin/HEAD` at the default branch, or anything built on it still resolves against `main`:

```bash
git fetch origin && git remote set-head origin -a
git push -u origin <branch-name>
gh pr create --title "..." --body "..."
```

### The promotion App (admin setup)

`promote.yml` pushes as a GitHub App, because `main`'s ruleset lets only that App's bypass entry update it. It is the same App the reuben repo promotes with. To set it up on another repo, or to rotate its key:

1. **Install** the App on the repo: Org settings → Developer settings → GitHub Apps → the App → Install App → Configure → Repository access. It needs only **Contents: Read and write**.
2. **Secrets:** `PROMOTE_APP_ID` holds the App's **Client ID** (`Iv23…`, from its General page; the workflow passes it as `client-id`), and `PROMOTE_APP_PRIVATE_KEY` holds a private key's `.pem`. A key cannot be read back out of another repo's secrets; generate a new one on the App's page if needed. An App can have several active keys, so this breaks no other repo.
3. **Bypass:** add the App to the `main` ruleset's bypass list with *Always allow*. It is the only bypass entry. `main`'s ruleset deliberately has no "require a pull request" rule, which would block the promotion push.

All three are admin-only: an agent can neither read nor set secrets, nor read or edit a ruleset's bypass list.

### If `main` diverges

Promotion fails with *Cannot fast-forward* when something landed on `main` other than by promotion. Merging `main` back into `dev` cannot fix it: `dev` takes only squash-merged PRs, so the merge commit never reaches `dev` and `main`'s tip stays unreachable. Instead:

1. re-land whatever went onto `main` as an ordinary PR into `dev` (cherry-pick it), then
2. an admin moves `main` back to a commit on `dev`. That is a non-fast-forward push, which `main`'s ruleset blocks, so it needs the ruleset briefly disabled.

Step 2 is admin-only. An agent hands it off rather than improvising.

## Issues

Issues and PRDs are GitHub Issues on `Impractical-Instruments/CommunityGarden`. Use the `gh` CLI. Where a skill says "publish to the issue tracker", create an issue; where it says "fetch the ticket", view one.

- **Create:** `gh issue create --title "..." --body "..." --label "..."`
- **Read:** `gh issue view <number>` (add `--json title,body,labels,state` for parseable output)
- **List:** `gh issue list --state open --label needs-triage`
- **Comment:** `gh issue comment <number> --body "..."`
- **Label:** `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close:** `gh issue close <number> --comment "..."`

Pass a multi-line body through a heredoc, `--body "$(cat <<'EOF'` … `EOF` `)"`, so its formatting survives.

## Triage labels

| Label | Meaning |
|---|---|
| `needs-triage` | Maintainer needs to evaluate this issue |
| `needs-info` | Waiting on reporter for more information |
| `ready-for-agent` | Fully specified, ready for an AFK agent |
| `ready-for-human` | Requires human implementation |
| `wontfix` | Will not be actioned |
