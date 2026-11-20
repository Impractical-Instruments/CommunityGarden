# Git Workflow

## Private show content

`ShowControl/FundingCAPTCHA/images/private/` is a clone of a separate private repo and must never be staged, committed, or referenced by name in this one; see `docs/FundingCAPTCHA.md`. `make setup` installs the pre-commit hook that guards it.

## Branches

**`dev` is the integration branch and the default; `main` is what the show machines run.** See [ADR-0027](../adr/0027-dev-integrates-main-is-promoted.md).

- **Branch off `dev` and open every PR against `dev`.** Its ruleset requires a PR, squash merge, linear history and the `test` check from `tests.yml`. Nobody commits to `dev` directly.
- **Name the issues a PR closes** in its body.
- **`main` moves only by promotion.** Actions → *Promote dev to main* → Run workflow ([`promote.yml`](../../.github/workflows/promote.yml)) fast-forwards `main` to `dev`. No PR targets `main`, and its ruleset blocks every push except the promotion App's. A show machine that updates with `git pull` gets the last promoted `dev`.
- **Once per clone**, run `git fetch origin && git remote set-head origin -a`, or `origin/HEAD` and anything built on it still resolve against `main`.
- **A failed promotion, the promotion App and `main`'s ruleset are admin-only.** Hand them off; the steps are in [ADR-0027](../adr/0027-dev-integrates-main-is-promoted.md#the-promotion-app-admin-setup).

## Issues

Issues and PRDs are GitHub Issues on `Impractical-Instruments/CommunityGarden`, through the `gh` CLI. Where a skill says "publish to the issue tracker", create an issue; where it says "fetch the ticket", view one.

## Triage labels

| Label | Meaning |
|---|---|
| `needs-triage` | Maintainer needs to evaluate this issue |
| `needs-info` | Waiting on reporter for more information |
| `ready-for-agent` | Fully specified, ready for an AFK agent |
| `ready-for-human` | Requires human implementation |
| `wontfix` | Will not be actioned |
