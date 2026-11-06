# MyGIt · Upstream synchronization strategy

This fork is based on [SourceGit](https://github.com/sourcegit-scm/sourcegit) (MIT).

## Branch responsibilities

| Branch | Purpose |
|---|---|
| `master` | Upstream stable/release baseline, unchanged by MyGIt UI work |
| `develop` | Upstream `sourcegit-scm/sourcegit:develop` tracking branch; keep it free of MyGIt-specific UI commits |
| `mygit` | MyGIt product/integration branch; this is the target of MyGIt feature PRs |
| `task/YYYYMMDD-HHMM-...` | Isolated feature work; merge to `mygit` only after requested review |

As of 2026-11-06, `mygit` and fork `develop` were created from `37bd1fbd8c56a872ebb6033c0639d3cb930f8aa9`. Upstream `develop` had advanced three commits to `76fe14863ac484635989a3feef36c4ff3c2f3dc7`. The three upstream commits touch `src/Commands/Command.cs`, `src/Models/User.cs`, and `src/ViewModels/DiffContext.cs`, which do not overlap the UI branch's changed file list. This lowers near-term conflict risk but is not a tested merge.

## Synchronization steps (manual, non-destructive)

Start in a clean local clone:

```bash
git remote add upstream https://github.com/sourcegit-scm/sourcegit.git
# Skip the line above if upstream already exists.
git fetch upstream develop
git switch develop
git merge --ff-only upstream/develop
git push origin develop

# After the product's changes have been merged into mygit:
git switch mygit
git merge --no-ff develop
# Resolve any overlaps in UI files, then compile/test before pushing.
git push origin mygit
```

If `git merge --ff-only` fails on `develop`, **stop**. It means this fork's tracking branch diverged and should be audited, not force-reset. If the product merge conflicts, resolve only those conflicts; never choose an entire side of a complex UI file without inspecting the source. Do not force-push or automatically merge `develop` into `mygit` without verifying existing MyGIt behavior.

For routine checks that do not change branch state:

```bash
git fetch upstream develop
git log --oneline develop..upstream/develop
git diff --stat develop..upstream/develop
```

## Minimize future conflicts

1. Keep product UI in new dedicated components, styles and namespaced resources wherever practical.
2. Keep changes to original `Commands/` and `Models/` minimal; adapt via view-model glue rather than forking Git protocol logic.
3. Prefer one product PR containing a small, functional change over a large UI rewrite for subsequent work.
4. Keep SourceGit licensing intact and avoid changing assembly/storage identifiers unless a migration plan exists.
5. Run .NET builds, static UI tests and Mac UI checks before merging. Upstream sync can be inspected earlier, but a successful Git merge alone is not a compatibility guarantee.

**Current limitation:** The six-screen UI change still modifies existing SourceGit XAML and view models directly. Future upstream edits to those same files may require manual conflict resolution. Keeping branches separate simplifies the process but cannot make it conflict-free.
