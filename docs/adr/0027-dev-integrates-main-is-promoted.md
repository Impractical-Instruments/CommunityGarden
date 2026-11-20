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
- If `main` ever diverges, recovery needs an admin; see [If `main` diverges](#if-main-diverges) below.

## The promotion App (admin setup)

`promote.yml` pushes as a GitHub App, because `main`'s ruleset lets only that App's bypass entry update it. It is the same App the reuben repo promotes with. To set it up on another repo, or to rotate its key:

1. **Install** the App on the repo: Org settings → Developer settings → GitHub Apps → the App → Install App → Configure → Repository access. It needs only **Contents: Read and write**.
2. **Secrets:** `PROMOTE_APP_ID` holds the App's **Client ID** (`Iv23…`, from its General page; the workflow passes it as `client-id`), and `PROMOTE_APP_PRIVATE_KEY` holds a private key's `.pem`. A key cannot be read back out of another repo's secrets; generate a new one on the App's page if needed. An App can have several active keys, so this breaks no other repo.
3. **Bypass:** add the App to the `main` ruleset's bypass list with *Always allow*. It is the only bypass entry. `main`'s ruleset deliberately has no "require a pull request" rule, which would block the promotion push.

All three are admin-only: an agent can neither read nor set secrets, nor read or edit a ruleset's bypass list.

## If `main` diverges

Promotion fails with *Cannot fast-forward* when something landed on `main` other than by promotion. Merging `main` back into `dev` cannot fix it: `dev` takes only squash-merged PRs, so the merge commit never reaches `dev` and `main`'s tip stays unreachable. Instead:

1. re-land whatever went onto `main` as an ordinary PR into `dev` (cherry-pick it), then
2. an admin moves `main` back to a commit on `dev`. That is a non-fast-forward push, which `main`'s ruleset blocks, so it needs the ruleset briefly disabled.

Step 2 is admin-only. An agent hands it off rather than improvising.
