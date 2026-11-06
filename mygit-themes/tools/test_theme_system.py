#!/usr/bin/env python3
"""Dependency-free tests for the two-layer MyGIt theme contract.

Run from the repository root:
    python3 -m unittest discover -s mygit-themes/tools -p 'test_*.py'
"""

import importlib.util
import json
import pathlib
import sys
import unittest

TOOLS = pathlib.Path(__file__).resolve().parent
PACK = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import layout  # noqa: E402
import theme   # noqa: E402


class MyGItThemeTests(unittest.TestCase):
    def test_manifest_has_complete_design_and_classic(self):
        data = layout.manifest()
        self.assertEqual(data["defaultLayout"], "mygit-design")
        profiles = {profile["id"]: profile for profile in data["layouts"]}
        self.assertEqual(set(profiles), {"mygit-design", "upstream-classic"})
        self.assertTrue(profiles["mygit-design"]["requiresRebuild"])
        self.assertEqual(len(profiles["mygit-design"]["screens"]), 6)
        self.assertEqual(profiles["upstream-classic"]["patches"], [])

    def test_all_six_patch_modules_are_present_and_do_not_overlap(self):
        profiles = layout.validate()
        self.assertEqual(len(profiles["mygit-design"]), 6)
        self.assertEqual(profiles["upstream-classic"], [])
        paths = set()
        for file in profiles["mygit-design"]:
            headers = layout.PATCH_HEADER.findall(file.read_text(encoding="utf-8"))
            for path in headers:
                self.assertNotIn(path, paths)
                self.assertTrue(path.startswith("src/"))
                self.assertFalse(path.startswith(("src/Commands/", "src/Models/")))
                paths.add(path)
        self.assertEqual(len(paths), 48)

    def test_native_light_and_dark_appearance_presets(self):
        entries = theme.validate()
        self.assertEqual({preset["id"] for preset in entries}, {"light", "dark"})
        for item in entries:
            path = theme.preset_path(item)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("BasicColors", data)
            self.assertGreaterEqual(len(data["BasicColors"]), 30)
            self.assertGreaterEqual(len(data["GraphColors"]), 6)

    def test_layout_paths_cannot_escape_theme_directory(self):
        malicious = {
            "id": "mygit-design",
            "type": "isolated-source-overlay",
            "patches": ["layouts/mygit-design/patches/../../../../src/App.axaml"],
        }
        with self.assertRaises(layout.LayoutError):
            layout.profile_patches(malicious)


if __name__ == "__main__":
    unittest.main()
