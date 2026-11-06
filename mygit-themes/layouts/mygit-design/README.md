# MyGIt Design · Layout Theme

This is the implementation package for the six approved MyGIt UI mockups, **not** a replacement Git engine. All SourceGit backend operations remain upstream-owned.

| Original mockup | Theme patch | Layout introduced |
|---|---|---|
| 01 · Workspace | `10-shell-home.patch` | Workspace home, recent repository cards, search, groups |
| 02 · Changes | `20-working-copy.patch` | Changes / Diff / permanent commit composer |
| 03 · History | `30-history-branches.patch` | Commit graph with adjacent details |
| 04 · Branches | `30-history-branches.patch` | Branches and worktrees management overview |
| 05 · Conflicts | `40-conflicts-settings.patch` | Mine/Theirs/Result pane layout |
| 06 · Settings | `40-conflicts-settings.patch` | Wide settings window with left navigation |

The `00-adapters.patch` bundle contains only the UI wiring needed for the redesigned navigation and recent repositories. The `50-visual-resources.patch` bundle carries the theme tokens, styles and localized labels.

These patches were extracted from `task/20261106-1718-workspace-navigation-redesign`, originally based on `develop@37bd1fbd`. They are only applied to a separate detached Git worktree after compatibility checks; production `develop` and `mygit` remain unchanged. Light/Dark colors are native SourceGit overrides, but layout changes require rebuilding. The actual .NET build and rendered Mac screenshot comparison are pending owner acceptance.

```bash
python3 mygit-themes/tools/theme.py validate
python3 mygit-themes/tools/theme.py check mygit-design
python3 mygit-themes/tools/theme.py prepare mygit-design --output ../MyGIt-Design
```
