# MyGIt · Native Theme Pack

> **MyGIt now follows SourceGit, not a long-lived UI fork.** Only this directory contains MyGIt-specific deliverables. No SourceGit C#, XAML, Git commands, application identifiers or runtime behavior need to be changed.

[中文说明](README_cn.md) · [Upstream SourceGit](https://github.com/sourcegit-scm/sourcegit) · [Upstream theme specification](https://github.com/sourcegit-scm/sourcegit-theme)

## Design goal

Keep SourceGit's current GUI and Git functionality intact; make MyGIt visually cohesive through its already-supported **Theme Overrides** JSON interface. The themes cover surfaces, text, buttons, separators, Diff, conflicts, highlights and history graph colors.

- **MyGIt Light** — light, calm macOS-like neutral surfaces and indigo accent (recommended).
- **MyGIt Dark** — deep midnight blue, balanced text contrast and indigo accent.

This pack **does not** change layout, create a three-column commit screen, add a recent-repository toolbar dropdown, or replace SourceGit windows. Those features require an upstream implementation. The previous UI overhaul remains preserved on its task branch as reference and is intentionally not merged into this product branch.

## Use it (no rebuild, no patch)

1. Download [MyGIt-Light.json](presets/MyGIt-Light.json) or [MyGIt-Dark.json](presets/MyGIt-Dark.json). Or check out the `mygit` branch and use the file directly.
2. Launch the unmodified SourceGit app.
3. Open **Preferences → Appearance**.
4. Set **Theme** to **Light** or **Dark** to match the preset.
5. Under **Theme Overrides**, select the matching JSON file.

SourceGit loads and persists the file path through its native preferences. You can switch or revert anytime from that same screen; to revert, clear **Theme Overrides**.

### Optional helper (Python 3.9+, no third-party packages)

```bash
python3 mygit-themes/tools/theme.py list
python3 mygit-themes/tools/theme.py validate
python3 mygit-themes/tools/theme.py install light
python3 mygit-themes/tools/theme.py install dark
```

The helper only copies the selected JSON to a stable `SourceGit/Themes` folder under the system's normal SourceGit config directory and prints the path to select. It does **not** edit `preference.json`, modify the executable, change Git configuration, or restart SourceGit. For updating an existing installed preset, explicitly pass `--force`. On machines without Python, download and select the JSON manually.

## Theme contract

```text
mygit-themes/
├── manifest.json                # versioned preset registry; NOT read by SourceGit
├── presets/
│   ├── MyGIt-Light.json         # official ThemeOverrides payload
│   └── MyGIt-Dark.json          # official ThemeOverrides payload
├── tools/theme.py               # optional installer and validation
├── README.md
└── README_cn.md
```

Theme files use exactly SourceGit's `ThemeOverrides` fields: `BasicColors`, `GraphPenThickness`, `OpacityForNotMergedCommits`, and `GraphColors`. `BasicColors` supports the names that SourceGit exposes in `src/Resources/Themes.axaml`, as well as `SystemAccentColor`. Preset colors use explicit `#AARRGGBB` strings for consistent opacity. `manifest.json` belongs to this theme pack only and does not require an upstream plugin, installation hook, or application patch.

For new themes: add one independent JSON file under `presets/`, register its id/path/base theme in `manifest.json`, and run the validator. These are the only files that normally need maintenance.

## Upstream sync without a UI fork

`master` remains the upstream stable fork branch and `develop` follows SourceGit's develop branch; MyGIt-specific files stay in `mygit-themes/` on the `mygit` branch. After a clean upstream fast-forward:

```bash
git remote add upstream https://github.com/sourcegit-scm/sourcegit.git  # once
git fetch upstream develop
git switch develop
git merge --ff-only upstream/develop
git push origin develop

git switch mygit
git merge --no-ff develop
python3 mygit-themes/tools/theme.py validate
git push origin mygit
```

Skip `remote add` when already configured. If any upstream fast-forward or product merge conflicts, stop and review rather than force-pushing. Nothing in this theme pack needs to be applied to SourceGit's source files.

**Status:** Native schema and design token validation is in place. Actual SourceGit rendering on macOS/Windows/Linux is for owner acceptance; a valid JSON file is not evidence of visual parity with the earlier screenshots.
