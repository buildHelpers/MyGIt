#!/usr/bin/env python3
"""Package-contract tests; these do not claim desktop rendering validation."""
import json
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import layout
import theme


class MyGItThemeTests(unittest.TestCase):
    def test_manifest_has_design_and_classic(self):
        data = layout.manifest()
        self.assertEqual(data['defaultLayout'], 'mygit-design')
        profiles = {p['id']: p for p in data['layouts']}
        self.assertEqual(set(profiles), {'mygit-design', 'upstream-classic'})
        self.assertTrue(profiles['mygit-design']['requiresRebuild'])
        self.assertEqual(len(profiles['mygit-design']['screens']), 6)
        self.assertEqual(profiles['upstream-classic']['patches'], [])

    def test_ordered_integration_targets_are_declared(self):
        profile = layout.find_profile('mygit-design')
        profiles = layout.validate()
        self.assertEqual(len(profiles['mygit-design']), 13)
        self.assertEqual(profiles['upstream-classic'], [])
        targets = layout.validate_patch_sequence(profile, profiles['mygit-design'])
        self.assertEqual(len(targets), 53)
        self.assertIn('src/Views/WorkingCopy.axaml.cs', targets)
        integration = 'layouts/mygit-design/patches/60-integration.patch'
        self.assertEqual(set(profile['revisions'][integration]), {
            'src/Views/Launcher.axaml', 'src/Views/Launcher.axaml.cs',
            'src/Views/Repository.axaml', 'src/Views/Histories.axaml',
        })
        self.assertEqual(profile['revisions']['layouts/mygit-design/patches/70-branches-search.patch'], [
            'src/ViewModels/Repository.cs', 'src/Views/BranchesOverview.axaml',
            'src/Views/BranchesOverview.axaml.cs',
        ])
        self.assertEqual(profile['revisions']['layouts/mygit-design/patches/71-workspace-dashboard.patch'], [
            'src/Views/Welcome.axaml', 'src/ViewModels/Welcome.cs',
        ])
        self.assertEqual(profile['revisions']['layouts/mygit-design/patches/72-conflict-three-columns.patch'],
                         ['src/Views/MergeConflictEditor.axaml'])
        self.assertEqual(profile['revisions']['layouts/mygit-design/patches/73-settings-preview.patch'],
                         ['src/Views/Preferences.axaml'])
        self.assertEqual(profile.get('assetGenerator'), 'tools/icons.py')
        self.assertEqual({
            'src/Native/MacOS.cs', 'src/Native/Windows.cs', 'src/Native/Linux.cs'
        }.issubset(targets), True)
        self.assertFalse(any(p.startswith(('src/Commands/', 'src/Models/')) for p in targets))

    def test_native_appearance_presets(self):
        entries = theme.validate()
        self.assertEqual({p['id'] for p in entries}, {'light', 'dark'})
        for entry in entries:
            data = json.loads(theme.preset_path(entry).read_text(encoding='utf-8'))
            self.assertGreaterEqual(len(data['BasicColors']), 30)
            self.assertGreaterEqual(len(data['GraphColors']), 6)


    def test_icon_formats_and_dimensions(self):
        import struct
        import icons
        png = icons.render_png(32)
        self.assertTrue(png.startswith(icons.PNG_SIGNATURE))
        self.assertEqual(struct.unpack(">II", png[16:24]), (32, 32))
        images = {size: icons.render_png(size) for size in (16, 32, 48, 64, 128, 256)}
        ico = icons.make_ico(images)
        self.assertEqual(ico[:4], b"\x00\x00\x01\x00")
        self.assertEqual(struct.unpack("<H", ico[4:6])[0], 6)
        self.assertTrue((layout.THEMES_DIR / 'assets/MyGIt-icon.svg').is_file())

    def test_layout_path_cannot_escape_theme_directory(self):
        malicious = {'id': 'mygit-design', 'type': 'isolated-source-overlay',
                     'patches': ['layouts/mygit-design/patches/../../../../src/App.axaml']}
        with self.assertRaises(layout.LayoutError):
            layout.profile_patches(malicious)


if __name__ == '__main__':
    unittest.main()
