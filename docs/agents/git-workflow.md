# Git Workflow

- **Private show content:** `ShowControl/FundingCAPTCHA/images/private/` is a clone of a separate private repo and must never be staged, committed, or referenced by name in this one — see `docs/FundingCAPTCHA.md`. Install the guard hook once per clone with `bash scripts/install-git-hooks.sh`.
- **Main branch:** `main`
- **Feature branches:** descriptive names, typically prefixed with the author or tool (e.g. `claude/update-osc-schema-xY3kQ`)
- **Never commit directly to `main`.** Branch off `main`, commit there, push, and open a pull request. Work lands through review, not straight to the trunk.
- **Open the PR with `gh pr create`**, summarising the work and naming the issues it closes.

```bash
git push -u origin <branch-name>
gh pr create --title "..." --body "..."
```
