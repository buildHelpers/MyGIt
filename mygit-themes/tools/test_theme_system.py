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
        self.assertEqual(len(profiles['mygit-design']), 7)
        self.assertEqual(profiles['upstream-classic'], [])
        targets = layout.validate_patch_sequence(profile, profiles['mygit-design'])
        self.assertEqual(len(targets), 49)
        self.assertIn('src/Views/WorkingCopy.axaml.cs', targets)
        last = profiles['mygit-design'][-1].relative_to(layout.THEMES_DIR).as_posix()
        self.assertEqual(set(profile['revisions'][last]), {
            'src/Views/Launcher.axaml', 'src/Views/Launcher.axaml.cs',
            'src/Views/Repository.axaml', 'src/Views/Histories.axaml',
        })
        self.assertFalse(any(p.startswith(('src/Commands/', 'src/Models/')) for p in targets))

    def test_native_appearance_presets(self):
        entries = theme.validate()
        self.assertEqual({p['id'] for p in entries}, {'light', 'dark'})
        for entry in entries:
            data = json.loads(theme.preset_path(entry).read_text(encoding='utf-8'))
            self.assertGreaterEqual(len(data['BasicColors']), 30)
            self.assertGreaterEqual(len(data['GraphColors']), 6)

    def test_layout_path_cannot_escape_theme_directory(self):
        malicious = {'id': 'mygit-design', 'type': 'isolated-source-overlay',
                     'patches': ['layouts/mygit-design/patches/../../../../src/App.axaml']}
        with self.assertRaises(layout.LayoutError):
            layout.profile_patches(malicious)


if __name__ == '__main__':
    unittest.main()
