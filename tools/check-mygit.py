#!/usr/bin/env python3
"""Dependency-free static checks for the direct-source MyGIt product.

Run: python3 tools/check-mygit.py
Checks structure and wiring, NOT runtime GUI or .NET compilation.
"""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
A = "{https://github.com/avaloniaui}"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(detail)


def main() -> int:
    for path in (
        "src/App.axaml",
        "src/Views/Launcher.axaml",
        "src/Views/Repository.axaml",
        "src/Views/Welcome.axaml",
        "src/Views/WorkingCopy.axaml",
        "src/Views/Histories.axaml",
        "src/Views/BranchesOverview.axaml",
        "src/Views/MergeConflictEditor.axaml",
        "src/Views/Preferences.axaml",
        "src/Resources/Styles.axaml",
        "src/Resources/Themes.axaml",
        "src/SourceGit.csproj",
        "build/resources/app/App.plist",
    ):
        ET.parse(ROOT / path)
    print("PASS: XAML, project and macOS property-list XML parse")

    title = ET.fromstring(read("src/Views/Launcher.axaml"))
    buttons = list(title.iter(A + "Button"))
    pickers = [item for item in buttons if item.get("Click") == "OnOpenPagesCommandPalette"]
    require(len(pickers) == 1, "Only one repository switcher should be visible")
    require(pickers[0].get("HotKey") == "{OnPlatform Ctrl+P, macOS=⌘+P}",
            "The single repo picker must retain the original shortcut")
    require(title.find(".//" + A + "LauncherTabBar") is None or
            "Width=\"220\"" in read("src/Views/Launcher.axaml"),
            "Repository tabs should remain accessible without crowding the titlebar")
    print("PASS: unified top search and repository tab access")

    repo = ET.fromstring(read("src/Views/Repository.axaml"))
    nav = [x for x in repo.iter(A + "ListBox")
           if x.get("SelectedIndex") == "{Binding SelectedViewIndex, Mode=TwoWay}"]
    require(len(nav) == 1, "Duplicate section-navigation control")
    require(len(list(nav[0].iter(A + "ListBoxItem"))) == 4,
            "SelectedViewIndex maps exactly four repository sections")
    require("DisplayName" in read("src/ViewModels/Repository.cs"),
            "Repository identity must show the actual project name, not a fixed label")
    require("Icons.Histories" in read("src/Views/Repository.axaml"),
            "History requires its own visible navigation icon")
    print("PASS: persistent repository navigation and actual repository identity")

    working = ET.fromstring(read("src/Views/WorkingCopy.axaml"))
    grids = [node for node in working.iter(A + "Grid")
             if node.get("SizeChanged") == "OnMainLayoutSizeChanged"]
    require(len(grids) == 1 and len(list(grids[0].find(A + "Grid.ColumnDefinitions"))) == 5,
            "Working copy should have changes / diff / composer plus splitters")
    require("Click=\"OnCheckoutBranch\"" in read("src/Views/BranchesOverview.axaml"),
            "Branch management must expose the existing checkout confirmation")
    require("BranchSearchText" in read("src/ViewModels/Repository.cs"),
            "Branch search should use the real repository model")
    require('ColumnDefinitions="*,*,*,22"' in read("src/Views/MergeConflictEditor.axaml"),
            "Merge editor must use three side-by-side panes")
    require("MyGItThemePresets.TryInstall" in read("src/Views/Preferences.axaml.cs"),
            "Light/Dark theme cards must activate the actual JSON presets")
    print("PASS: direct-source working copy, branches, conflicts and appearance wiring")

    ipc = read("src/Models/IpcChannel.cs")
    require('return "MyGIt";' in ipc and '"mygit.instance.lock"' in ipc
            and 'return $"MG_{hash}";' in ipc,
            "Application IPC must not reuse SourceGit's pipe or Linux runtime lock")
    native = read("src/Native/MacOS.cs")
    require('"MyGIt"' in native, "macOS preference root must be independent")
    plist = read("build/resources/app/App.plist")
    require("<string>com.buildhelpers.mygit</string>" in plist and
            "<string>MyGIt</string>" in plist,
            "macOS package identity must not equal SourceGit")
    project = read("src/SourceGit.csproj")
    require("<DisableUpdateDetection>true</DisableUpdateDetection>" in project,
            "MyGIt must not display unrelated SourceGit version updates")
    print("PASS: independent app identity, preferences, IPC and update safety")

    packaging = read("tools/build-mygit.sh")
    require("dotnet publish" in packaging and "MyGIt.app" in packaging and
            "git apply" not in packaging and "theme.py prepare" not in packaging,
            "The only MyGIt Mac build must use directly modified src/ (no patches)")
    print("PASS: single macOS build entry (static check only)")
    print("NOT_RUN: .NET compile, macOS application launch, visual screenshot parity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
