#!/usr/bin/env python3
"""Validate and install MyGIt appearance-only SourceGit theme overrides.

This tool never alters SourceGit binaries, Git repositories or preference.json.
The final selection is made in SourceGit > Preferences > Appearance.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

PACK = Path(__file__).resolve().parents[1]
REPOSITORY = PACK.parent
MANIFEST = PACK / "manifest.json"
COLOR = re.compile(r"^#[A-Fa-f0-9]{6}(?:[A-Fa-f0-9]{2})?$")
RESOURCE = re.compile(r'<Color x:Key="Color\.([^"]+)"')
THEME_PROPERTIES = {
    "BasicColors", "GraphPenThickness", "OpacityForNotMergedCommits", "GraphColors"
}


def app_config_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "SourceGit"
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise ValueError("APPDATA is not set; specify --target-dir instead")
        return Path(appdata) / "SourceGit"
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "SourceGit"


def load_manifest() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("formatVersion") != 1 or not isinstance(data.get("presets"), list):
        raise ValueError("Unsupported or malformed theme manifest")
    ids = [p.get("id") for p in data["presets"]]
    if not ids or len(set(ids)) != len(ids) or not all(isinstance(i, str) for i in ids):
        raise ValueError("Theme ids must be non-empty and unique")
    return data


def declared_upstream_colors() -> set[str]:
    """Read theme keys from the checked-out upstream source, without changing it."""
    themes = REPOSITORY / "src" / "Resources" / "Themes.axaml"
    if not themes.exists():
        return set()
    return set(RESOURCE.findall(themes.read_text(encoding="utf-8-sig")))


def preset_path(preset: dict) -> Path:
    path = preset.get("file")
    if not isinstance(path, str) or not path.startswith("presets/"):
        raise ValueError("Theme file must live under presets/")
    full = (PACK / path).resolve()
    if not full.is_relative_to((PACK / "presets").resolve()) or full.suffix.lower() != ".json":
        raise ValueError("Invalid theme file path")
    return full


def validate() -> list[dict]:
    manifest = load_manifest()
    known = declared_upstream_colors()
    for p in manifest["presets"]:
        if p.get("baseTheme") not in ("Light", "Dark"):
            raise ValueError(f"Invalid baseTheme for {p.get('id')}")
        file = preset_path(p)
        theme = json.loads(file.read_text(encoding="utf-8"))
        if set(theme) - THEME_PROPERTIES:
            raise ValueError(f"Unsupported properties in {file}")
        colors = theme.get("BasicColors")
        if not isinstance(colors, dict) or not colors:
            raise ValueError(f"Missing BasicColors in {file}")
        for key, value in colors.items():
            if not isinstance(key, str) or not isinstance(value, str) or not COLOR.fullmatch(value):
                raise ValueError(f"Invalid theme color {key!r}: {value!r}")
            if known and key not in known and key != "SystemAccentColor":
                raise ValueError(f"Unknown SourceGit color key {key!r} in {file}")
        graph = theme.get("GraphColors")
        if not isinstance(graph, list) or not graph or not all(
            isinstance(color, str) and COLOR.fullmatch(color) for color in graph
        ):
            raise ValueError(f"Invalid GraphColors in {file}")
        weight = theme.get("GraphPenThickness", 2)
        opacity = theme.get("OpacityForNotMergedCommits", 0.5)
        if type(weight) not in (int, float) or not (1 <= weight <= 4):
            raise ValueError(f"Invalid GraphPenThickness in {file}")
        if type(opacity) not in (int, float) or not (0.1 <= opacity <= 1):
            raise ValueError(f"Invalid OpacityForNotMergedCommits in {file}")
        print(f"OK {p['id']} [{p['baseTheme']}] {file.relative_to(PACK)} ({len(colors)} colors)")
    return manifest["presets"]


def install(preset: dict, target: Path, force: bool) -> Path:
    src = preset_path(preset)
    dest = target.expanduser().resolve() / "Themes" / src.name
    content = src.read_bytes()
    if dest.exists():
        if dest.read_bytes() == content:
            print(f"Already installed: {dest}")
            return dest
        if not force:
            raise FileExistsError(f"{dest} exists with different content; rerun with --force")
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Atomic single-file replacement, no preference.json changes and no app restart.
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=dest.parent, prefix=dest.name + ".",
                                         suffix=".tmp", delete=False) as f:
            tmp = Path(f.name)
            f.write(content)
        tmp.replace(dest)
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="MyGIt native SourceGit theme pack")
    parser.add_argument("command", choices=["list", "validate", "install"])
    parser.add_argument("preset", nargs="?", help="Preset id: light or dark (install only)")
    parser.add_argument("--target-dir", type=Path,
                        help="SourceGit config directory (otherwise detected by OS)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite an existing copied preset; never edits preferences")
    args = parser.parse_args()
    try:
        presets = validate()
        if args.command == "list":
            for p in presets:
                print(f"{p['id']}: {p['name']} — Appearance > Theme: {p['baseTheme']}")
        elif args.command == "install":
            match = next((p for p in presets if p["id"] == args.preset), None)
            if match is None:
                parser.error("install requires a valid preset id: light or dark")
            target = args.target_dir if args.target_dir else app_config_dir()
            dest = install(match, target, args.force)
            print(f"Installed: {dest}")
            print("SourceGit > Preferences > Appearance:")
            print(f"  Theme = {match['baseTheme']}")
            print(f"  Theme Overrides = {dest}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
