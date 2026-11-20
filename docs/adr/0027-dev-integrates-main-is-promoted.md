# ADR 0027 — `dev` integrates; `main` moves only by promotion

**Status:** Accepted

## Context

Until 2026-11-20 every PR squash-merged straight into `main`, the default branch. `main` was also what a show machine got from `git pull` when it had internet (see [showtime.md](../showtime.md)). So every merge was, in effect, a release to the show, with no point at which to say "this is the state we stand behind".

reuben, which this repo vendors at `vendor/reuben`, already worked differently: `dev` integrates, and `main` advances only by a hand-dispatched fast-forward. Its other consumers work the same way.

## Decision

1. **`dev` is the default branch and the integration branch.** Every PR targets it. Its ruleset requires a PR, squash merge, linear history and the `test` check.
2. **`main` moves only by `promote.yml`,** a hand-dispatched workflow that fast-forwards `main` to `dev` and pushes as the promotion GitHub App. `main`'s ruleset blocks creation, update, deletion and force-push, with the App as its only bypass entry, and has no pull-request rule.
3. **`main` means "what the show machines run".** A box that updates with `git pull` follows `main`. `scripts/deploy.sh` is unchanged: it deploys whatever branch the laptop has checked out, over the show LAN.
4. **CI caches follow `dev`.** `testmon-data.yml` records on pushes to `dev`, because PR runs can read only caches saved on their base branch or the default branch, and both are now `dev`.

## Reasons

- **A deliberate release step.** Merging and shipping to the show become separate acts; a run of merges can land on `dev` and be promoted once it has been tried.
- **One model across the repos.** Same branch names, same promotion workflow and same App as reuben, so nothing new to learn or provision.
- **A fast-forward keeps the two branches identical.** No GitHub merge button does a true fast-forward; promoting by workflow keeps `main`'s commits exactly `dev`'s, so `main` is always an ancestor of `dev`.

## Consequences

- Nothing reaches `main`, or a show machine that pulls, until someone runs the promotion.
- Each clone has to run `git remote set-head origin -a` once, or `origin/HEAD` keeps resolving to `main`.
- If `main` ever diverges, recovery needs an admin; see [git-workflow.md](../agents/git-workflow.md#if-main-diverges).
