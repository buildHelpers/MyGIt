# MyGIt Design Theme System — work in progress

**Goal: layouts, navigation, control styles and Light/Dark palettes together. The current UI implementation is partial and does not yet reproduce all six approved mockups.**

[UI corrections and remaining gaps](UI_AUDIT.md) · [中文](README_cn.md)

## Architecture

`mygit-design` composes six initial UI overlays and an integration correction in a detached Git worktree, then builds there. `upstream-classic` keeps the original SourceGit layout. Light/Dark JSON files use the native Theme Overrides feature.

All custom assets stay in `mygit-themes/`; product `src/` remains upstream code. However, layout patches depend on upstream XAML and ViewModel structure and can need adaptation. This is **not maintenance-free and not runtime layout switching**.

The integration correction provides one repository picker and one Ctrl/Cmd+P binding, removes duplicated section navigation, aligns history headers/graph offsets, and updates three-pane working-copy sizing. Read the audit for remaining screen and icon work.

## Local use

Requires Git and Python 3.9+. Building requires .NET 10 and the upstream SourceGit dependencies. Run on a clean `mygit` checkout:

```bash
python3 mygit-themes/tools/theme.py layouts
python3 mygit-themes/tools/theme.py validate
python3 -m unittest discover -s mygit-themes/tools -p 'test_*.py'
python3 mygit-themes/tools/theme.py check mygit-design
python3 mygit-themes/tools/theme.py build mygit-design --output ../MyGIt-Design-Fixed
```

Output must be a new directory outside the source repository. To prepare without compiling:

```bash
python3 mygit-themes/tools/theme.py prepare mygit-design --output ../MyGIt-Design-Source
cd ../MyGIt-Design-Source
git submodule update --init --recursive
dotnet run --project src/SourceGit.csproj
```

For the original layout:

```bash
python3 mygit-themes/tools/theme.py prepare upstream-classic --output ../SourceGit-Classic
```

Pulling this branch does not update an existing generated worktree or installed application; generate and build a fresh one.

## Appearance and upstream updates

Select [MyGIt Light](presets/MyGIt-Light.json) or [MyGIt Dark](presets/MyGIt-Dark.json) in Preferences → Appearance, using the matching base theme and the JSON as Theme Overrides. Optional copying tool:

```bash
python3 mygit-themes/tools/theme.py install light
python3 mygit-themes/tools/theme.py install dark
```

The installer does not edit preferences or credentials. Color changes work at runtime; layout changes require rebuilding.

Keep `develop` aligned with upstream, merge into `mygit`, then run `check mygit-design`. Compatibility failures stop rather than overwrite. The seventh patch's revisions of earlier UI files must be declared precisely in the manifest.

**Validation:** New guard tests and patch application on retrieved source fixtures passed. Complete seven-patch assembly, .NET compilation, desktop launch and visual comparison are unverified. The new application icon is still a concept, not integrated platform assets.
