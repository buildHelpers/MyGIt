#!/usr/bin/env python3
"""Dependency-free static checks for the MyGIt desktop UI redesign.

Run at repository root:
    python3 tools/verify_mygit_ui.py

These checks cannot replace .NET 10 compilation or desktop interaction tests.
"""

import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
QUICK_REPO_KEYS = (
    "Button",
    "Title",
    "Hint",
    "Search",
    "Recent",
    "Open",
    "NoResults",
    "Keyboard",
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def check_xml() -> None:
    files = [
        "src/App.axaml",
        "src/Views/Launcher.axaml",
        "src/Views/Welcome.axaml",
        "src/Views/QuickRepositorySwitcher.axaml",
        "src/Views/Repository.axaml",
        "src/Views/WorkingCopy.axaml",
        "src/Views/Histories.axaml",
        "src/Views/BranchesOverview.axaml",
        "src/Views/MergeConflictEditor.axaml",
        "src/Views/Conflict.axaml",
        "src/Views/Preferences.axaml",
        "src/Views/RepositoryConfigure.axaml",
        "src/Views/StashesPage.axaml",
        "src/Views/DiffView.axaml",
        "src/Views/CommitDetail.axaml",
        "src/Views/RepositoryToolbar.axaml",
        "src/Views/LauncherPage.axaml",
        "src/Resources/Styles.axaml",
        "src/Resources/Themes.axaml",
        "src/SourceGit.csproj",
    ]
    files.extend(str(p.relative_to(ROOT)) for p in (ROOT / "src/Resources/Locales").glob("*.axaml"))

    for path in files:
        ET.parse(ROOT / path)
        print(f"PASS XML {path}")


def check_localization() -> None:
    locale_files = sorted((ROOT / "src/Resources/Locales").glob("*.axaml"))
    assert locale_files, "No locale files found"
    for path in locale_files:
        source = path.read_text(encoding="utf-8-sig")
        for key in QUICK_REPO_KEYS:
            marker = f'x:Key="Text.QuickRepo.{key}"'
            assert source.count(marker) == 1, (path, key)
    print(f"PASS quick repository localization in {len(locale_files)} locales")


def check_ui_handlers() -> None:
    for view, code, events in (
        (
            "src/Views/Launcher.axaml",
            "src/Views/Launcher.axaml.cs",
            {"Click": ("OnShowWorkspaceHome", "OnOpenWorkspaceMenu", "OnOpenRecentRepositories")},
        ),
        (
            "src/Views/Welcome.axaml",
            "src/Views/Welcome.axaml.cs",
            {"Click": ("OnCloneRepository", "OnOpenLocalRepository", "OnFocusRepositorySearch")},
        ),
        (
            "src/Views/QuickRepositorySwitcher.axaml",
            "src/Views/QuickRepositorySwitcher.axaml.cs",
            {"Tapped": ("OnRepositoryTapped",)},
        ),
        (
            "src/Views/BranchesOverview.axaml",
            "src/Views/BranchesOverview.axaml.cs",
            {
                "Click": ("OnRefreshRepository", "OnAddWorktree", "OnViewCurrentHead"),
                "DoubleTapped": ("OnBranchDoubleTapped", "OnWorktreeDoubleTapped"),
            },
        ),
        (
            "src/Views/Welcome.axaml",
            "src/Views/Welcome.axaml.cs",
            {"Tapped": ("OnRecentRepositoryTapped",)},
        ),
    ):
        markup = read(view)
        handlers = read(code)
        for event, names in events.items():
            for name in names:
                assert f'{event}="{name}"' in markup, (view, name)
                assert re.search(rf"\bvoid\s+{name}\s*\(", handlers), (code, name)
                print(f"PASS event {name}")


def check_safe_navigation() -> None:
    launcher = read("src/ViewModels/Launcher.cs")
    home = re.search(
        r"public void ShowWorkspaceHome\s*\(\)\s*\{(?P<body>.*?)"
        r"(?=\n        public void AddNewTab)",
        launcher,
        re.DOTALL,
    )
    assert home, "ShowWorkspaceHome method not found"
    body = home.group("body")
    assert "ActivePage = page" in body and "Pages.Insert(0, home)" in body
    assert "CloseRepositoryInTab" not in body and "Commands." not in body

    menu = read("src/Views/Launcher.axaml.cs")
    assert "launcher.SwitchWorkspace(workspace)" in menu
    assert "launcher.ShowWorkspaceHome()" in menu
    assert "LauncherPagesCommandPalette(launcher)" in menu
    assert "flyout.ShowAt(button)" in menu

    preferences = read("src/ViewModels/Preferences.cs")
    assert "RecentRepositories" in preferences and "RemoveRange" in preferences
    assert "RememberRepository(repo.FullPath)" in launcher

    quick_model = read("src/ViewModels/QuickRepositorySwitcher.cs")
    assert "preferences.RecentRepositories" in quick_model
    assert "workspace.Repositories" in quick_model
    assert "item.Name.Contains(filter" in quick_model
    assert "item.Path.Contains(filter" in quick_model
    assert "_launcher.OpenRepositoryInTab(item.Path, null)" in quick_model
    assert "Commands." not in quick_model

    quick_view = read("src/Views/QuickRepositorySwitcher.axaml.cs")
    assert "SearchBox.Focus" in quick_view
    assert "Key.Enter" in quick_view and "Key.Escape" in quick_view
    print("PASS non-destructive home, persisted recency and searchable switcher")


def check_design_surfaces() -> None:
    repository = read("src/Views/Repository.axaml")
    view_model = read("src/ViewModels/Repository.cs")
    working_copy = read("src/Views/WorkingCopy.axaml")
    settings = read("src/Views/Preferences.axaml")
    branches = read("src/Views/BranchesOverview.axaml")
    history = read("src/Views/Histories.axaml")

    assert "IsBranchesVisible" in repository and "IsBranchesVisible" in view_model
    assert "BranchesOverview" in repository
    assert 'Grid.Column="4"' in working_copy  # permanent right commit pane
    assert "CommitMessageToolBox" in working_copy
    assert "UseTwoColumnsLayoutInHistories" in history
    assert 'TabStripPlacement="Left"' in settings
    assert "OnBranchDoubleTapped" in branches
    assert "OnWorktreeDoubleTapped" in branches
    assert "RecentRepositories" in read("src/Views/Welcome.axaml")

    english = read("src/Resources/Locales/en_US.axaml")
    views = (
        "src/Views/Repository.axaml",
        "src/Views/WorkingCopy.axaml",
        "src/Views/BranchesOverview.axaml",
        "src/Views/MergeConflictEditor.axaml",
        "src/Views/Preferences.axaml",
        "src/Views/Welcome.axaml",
    )
    for view in views:
        for key in re.findall(r"\\{DynamicResource (Text\\.[\\w.]+)\\}", read(view)):
            assert f'x:Key="{key}"' in english, (view, key)

    print("PASS design surface and localization links")


def main() -> int:
    try:
        check_xml()
        check_localization()
        check_ui_handlers()
        check_safe_navigation()
        check_design_surfaces()
    except (AssertionError, ET.ParseError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS static UI checks; .NET build and GUI validation still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
