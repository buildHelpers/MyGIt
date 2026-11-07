#!/usr/bin/env python3
"""Compose the MyGIt layout in an isolated detached worktree.

Ordered integration patches may revise earlier UI patches only when the exact
revisited paths are declared in the manifest. Upstream checkouts stay unchanged.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

THEMES_DIR = Path(__file__).resolve().parents[1]
ROOT = THEMES_DIR.parent
MANIFEST_PATH = THEMES_DIR / "manifest.json"
PATCH_HEADER = re.compile(r"^diff --git a/(src/[^\s]+) b/\1$", re.MULTILINE)
HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class LayoutError(Exception):
    """Validation, compatibility, or non-destructive preparation failure."""


def manifest() -> dict:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if data.get("formatVersion") != 1 or not isinstance(data.get("layouts"), list):
        raise LayoutError("Expected a versioned layout list in manifest.json")
    ids = [item.get("id") for item in data["layouts"]]
    if not ids or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise LayoutError("Layout ids must be non-empty and unique")
    return data


def find_profile(profile_id: str) -> dict:
    for item in manifest()["layouts"]:
        if item["id"] == profile_id:
            return item
    raise LayoutError(f"Unknown layout {profile_id!r}; use 'layouts' to list choices")


def validate_hunk_counts(body: str, name: str) -> None:
    """Reject malformed unified diffs before invoking git worktree or git apply."""
    lines = body.splitlines()
    hunks = 0
    for i, line in enumerate(lines):
        match = HUNK_HEADER.match(line)
        if not match:
            continue
        hunks += 1
        expected_old = int(match.group(2) or 1)
        expected_new = int(match.group(4) or 1)
        actual_old = 0
        actual_new = 0
        for following in lines[i + 1:]:
            if following.startswith(('@@ ', 'diff --git ')):
                break
            if following.startswith(' '):
                actual_old += 1
                actual_new += 1
            elif following.startswith('-'):
                actual_old += 1
            elif following.startswith('+'):
                actual_new += 1
            elif following.startswith('\\'):
                continue
            elif following:
                raise LayoutError(f"Unexpected diff line in {name}: {following[:80]}")
        if (actual_old, actual_new) != (expected_old, expected_new):
            raise LayoutError(
                f"Corrupt hunk in {name} at line {i + 1}: "
                f"expected {expected_old}/{expected_new} lines, "
                f"actual {actual_old}/{actual_new}"
            )
    if not hunks:
        raise LayoutError(f"Missing unified diff hunks in {name}")


def profile_patches(profile: dict) -> list[Path]:
    paths = profile.get("patches")
    if not isinstance(paths, list):
        raise LayoutError("Layout patches must be a list")
    output = []
    for rel in paths:
        if not isinstance(rel, str) or not rel.startswith(f"layouts/{profile['id']}/patches/"):
            raise LayoutError(f"Invalid layout patch path: {rel!r}")
        file = (THEMES_DIR / rel).resolve()
        if not file.is_relative_to((THEMES_DIR / "layouts" / profile["id"] / "patches").resolve()):
            raise LayoutError(f"Patch escapes layout directory: {rel}")
        if file.suffix != ".patch" or not file.is_file():
            raise LayoutError(f"Patch not found: {rel}")
        body = file.read_text(encoding="utf-8")
        validate_hunk_counts(body, rel)
        headers = PATCH_HEADER.findall(body)
        if not headers or len(headers) != body.count("diff --git "):
            raise LayoutError(f"Invalid Git diff headers in {rel}")
        if not all(name.startswith("src/") and ".." not in PurePosixPath(name).parts and
                   not name.startswith(("src/Commands/", "src/Models/")) for name in headers):
            raise LayoutError(f"Theme may only patch UI source paths: {rel}")
        output.append(file)
    if profile.get("type") == "upstream-unchanged" and output:
        raise LayoutError("The upstream-classic layout must have no patches")
    return output


def validate_patch_sequence(profile: dict, files: list[Path]) -> set[str]:
    """Allow only explicitly declared revisions of previously patched UI files."""
    revisions = profile.get("revisions", {})
    if not isinstance(revisions, dict):
        raise LayoutError("Layout revisions must map patch paths to revised source paths")
    names = [file.relative_to(THEMES_DIR).as_posix() for file in files]
    if len(set(names)) != len(names) or set(revisions) - set(names):
        raise LayoutError("Duplicate patch or unknown revision patch")
    seen: set[str] = set()
    for name, file in zip(names, files):
        targets = PATCH_HEADER.findall(file.read_text(encoding="utf-8"))
        if len(set(targets)) != len(targets):
            raise LayoutError(f"Duplicate source entry inside patch: {name}")
        declared = revisions.get(name, [])
        if not isinstance(declared, list) or not all(isinstance(x, str) for x in declared):
            raise LayoutError(f"Invalid revision list for {name}")
        if len(set(declared)) != len(declared):
            raise LayoutError(f"Duplicate revision declaration for {name}")
        overlap = seen.intersection(targets)
        if overlap != set(declared):
            raise LayoutError(f"Unexpected or missing revised paths in {name}: {sorted(overlap ^ set(declared))}")
        seen.update(targets)
    return seen


def validate() -> dict[str, list[Path]]:
    data = manifest()
    profiles: dict[str, list[Path]] = {}
    for item in data["layouts"]:
        files = profile_patches(item)
        targets = validate_patch_sequence(item, files)
        profiles[item["id"]] = files
        print(f"OK layout {item['id']}: {len(files)} ordered patches, {len(targets)} source paths")
    default = data.get("defaultLayout")
    if default not in profiles:
        raise LayoutError(f"Unknown default layout {default!r}")
    return profiles


def git(cwd: Path, *args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def prepare(profile_id: str, dest: Path, source: Path = ROOT, build: bool = False) -> Path:
    profiles = validate()
    if profile_id not in profiles:
        raise LayoutError(f"Unknown layout {profile_id!r}")
    source = source.expanduser().resolve()
    dest = dest.expanduser().resolve()
    actual = Path(git(source, "rev-parse", "--show-toplevel", capture=True).stdout.strip()).resolve()
    if actual != source:
        raise LayoutError(f"Source must be the repository root, not {source}")
    if not (source / "src" / "SourceGit.csproj").is_file():
        raise LayoutError("The source directory is not a SourceGit checkout")
    if dest == source or dest.is_relative_to(source):
        raise LayoutError("Output must be outside the upstream/source checkout")
    if dest.exists():
        raise LayoutError(f"Output already exists; refusing to overwrite: {dest}")
    # Ignore untracked editor/test caches: the composer never touches them.
    # Tracked source modifications still block preparation, to preserve work.
    if git(source, "status", "--porcelain", "--untracked-files=no", capture=True).stdout.strip():
        raise LayoutError("Tracked source has uncommitted changes; commit or stash first")
    created = False
    try:
        git(source, "worktree", "add", "--detach", str(dest), "HEAD")
        created = True
        for patch in profiles[profile_id]:
            git(dest, "apply", "--check", "--whitespace=nowarn", str(patch))
            git(dest, "apply", "--whitespace=nowarn", str(patch))
            print(f"APPLIED {patch.relative_to(THEMES_DIR)}")
        if profile_id == "mygit-design":
            # Replace application resources only in the detached design worktree.
            # Upstream src/App.ico, macOS App.icns and Linux icons stay untouched.
            subprocess.run([sys.executable, str(THEMES_DIR / "tools" / "icons.py"),
                            "--root", str(dest)], check=True)
            subprocess.run([sys.executable, str(THEMES_DIR / "tools" / "verify_design.py"),
                            str(dest)], check=True)
    except (OSError, subprocess.CalledProcessError):
        if created:
            # Only remove the detached worktree created by this invocation.
            git(source, "worktree", "remove", "--force", str(dest))
        raise
    print(f"Prepared layout {profile_id} at {dest}")
    print("The upstream-tracking branch and checkout were not modified.")
    if build:
        dotnet = shutil.which("dotnet")
        if not dotnet:
            raise LayoutError(f".NET SDK not found. Prepared source remains at {dest}")
        git(dest, "submodule", "update", "--init", "--recursive")
        subprocess.run([dotnet, "build", "-c", "Release", "src/SourceGit.csproj"], cwd=dest, check=True)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="MyGIt complete design layout theme composer")
    parser.add_argument("action", choices=["layouts", "validate", "check", "prepare", "build"])
    parser.add_argument("layout", nargs="?", default=None, help="mygit-design or upstream-classic")
    parser.add_argument("--source", type=Path, default=ROOT, help="Clean SourceGit/MyGIt checkout root")
    parser.add_argument("--output", type=Path, help="New, nonexistent directory outside the source")
    args = parser.parse_args()
    try:
        if args.action in ("validate", "layouts"):
            layouts = validate()
            if args.action == "layouts":
                for name in layouts:
                    print(f"  {name}  {'(default)' if manifest().get('defaultLayout') == name else ''}")
            return 0
        profile_id = args.layout or manifest()["defaultLayout"]
        if args.action == "check":
            with tempfile.TemporaryDirectory(prefix="mygit-layout-check-") as temp:
                output = Path(temp) / "checkout"
                try:
                    prepare(profile_id, output, args.source, build=False)
                finally:
                    if output.exists() and (output / ".git").exists():
                        git(args.source.expanduser().resolve(), "worktree", "remove", "--force", str(output))
            print(f"PASS layout {profile_id} applies to this upstream checkout")
            return 0
        if args.output is None:
            parser.error("prepare/build requires --output (outside the source checkout)")
        prepare(profile_id, args.output, args.source, build=args.action == "build")
        return 0
    except (LayoutError, subprocess.CalledProcessError, ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
