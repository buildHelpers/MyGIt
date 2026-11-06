#!/usr/bin/env python3
"""Static guardrails for the first MyGIt workspace UI increment.

This does not replace compiling SourceGit with the .NET 10 SDK or GUI smoke testing.
Run from the repository root: python3 tools/verify_mygit_ui.py
"""

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def check_xml() -> None:
    paths = [
        "src/App.axaml",
        "src/Views/Launcher.axaml",
        "src/Views/Welcome.axaml",
        "src/Resources/Styles.axaml",
        "src/Resources/Themes.axaml",
        "src/SourceGit.csproj",
    ]
    for path in paths:
        ET.parse(ROOT / path)
        print(f"PASS XML {path}")


def check_ui_handlers() -> None:
    for view, code, names in (
        (
            "src/Views/Launcher.axaml",
            "src/Views/Launcher.axaml.cs",
            ("OnShowWorkspaceHome", "OnOpenWorkspaceMenu"),
        ),
        (
            "src/Views/Welcome.axaml",
            "src/Views/Welcome.axaml.cs",
            ("OnCloneRepository", "OnOpenLocalRepository", "OnFocusRepositorySearch"),
        ),
    ):
        markup = read(view)
        handlers = read(code)
        for name in names:
            assert f'Click="{name}"' in markup, (view, name)
            assert re.search(rf"\\bvoid\\s+{name}\\s*\\(", handlers), (code, name)
            print(f"PASS event {name}")


def check_safe_navigation() -> None:
    launcher = read("src/ViewModels/Launcher.cs")
    match = re.search(
        r"public void ShowWorkspaceHome\\s*\\(\\)\\s*\\{(?P<body>.*?)"
        r"(?=\\n        public void AddNewTab)",
        launcher,
        re.DOTALL,
    )
    assert match, "ShowWorkspaceHome method not found"
    body = match.group("body")
    assert "ActivePage = page" in body and "Pages.Insert(0, home)" in body
    assert "CloseRepositoryInTab" not in body
    assert "Commands." not in body
    menu = read("src/Views/Launcher.axaml.cs")
    assert "launcher.SwitchWorkspace(workspace)" in menu
    assert "launcher.ActivePage = page" in menu
    assert "LauncherPagesCommandPalette(launcher)" in menu
    print("PASS navigation invariants")


def main() -> int:
    try:
        check_xml()
        check_ui_handlers()
        check_safe_navigation()
    except (AssertionError, ET.ParseError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS all static MyGIt UI checks; .NET build and GUI tests still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
