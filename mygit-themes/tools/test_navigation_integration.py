"""Regression tests for navigation checks and explicitly ordered UI corrections."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout
import verify_design

MARKUP = '''<Window xmlns="https://github.com/avaloniaui">
<Grid Grid.Row="0" ColumnDefinitions="Auto,Auto,Auto,*">
<Button Grid.Column="0" Click="OnShowWorkspaceHome"/>
<Button Grid.Column="1" Click="OnOpenWorkspaceMenu"/>
<Button Grid.Column="2" Click="OnOpenPagesCommandPalette" HotKey="{OnPlatform Ctrl+P, macOS=⌘+P}"/>
</Grid></Window>'''
HANDLER = '''private void OnOpenPagesCommandPalette(object sender, RoutedEventArgs e)
{ OnOpenRecentRepositories(sender, e); }'''
HISTORY = '''<Grid xmlns="https://github.com/avaloniaui" xmlns:v="using:SourceGit.Views">
<v:HistoriesCommitList ColumnHeaderHeight="32"/>
<Border Height="32" PointerPressed="OnCommitListHeaderPointerPressed"/>
<v:CommitGraph Margin="0,32,0,0"/>
</Grid>'''


class NavigationIntegrationTests(unittest.TestCase):
    def test_single_entry_passes(self):
        verify_design.check_navigation(MARKUP, HANDLER)

    def test_duplicate_old_and_new_entries_fail(self):
        markup = MARKUP.replace('</Grid>', '<Button Click="OnOpenRecentRepositories"/></Grid>')
        with self.assertRaisesRegex(ValueError, 'one repository switcher'):
            verify_design.check_navigation(markup, HANDLER)

    def test_duplicate_shortcut_fails(self):
        markup = MARKUP.replace('</Grid>', '<Button HotKey="{OnPlatform Ctrl+P, macOS=⌘+P}"/></Grid>')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            verify_design.check_navigation(markup, HANDLER)

    def test_keyboard_and_click_must_share_handler(self):
        with self.assertRaisesRegex(ValueError, 'same repository panel'):
            verify_design.check_navigation(MARKUP, HANDLER.replace('OnOpenRecentRepositories(sender, e);', 'OpenSomethingElse();'))

    def test_orphaned_caption_column_fails(self):
        with self.assertRaisesRegex(ValueError, 'Orphaned'):
            verify_design.check_navigation(MARKUP.replace('Grid.Column="2"', 'Grid.Column="7"'), HANDLER)

    def test_aligned_history_passes(self):
        verify_design.check_graph(HISTORY)

    def test_old_graph_offset_fails(self):
        with self.assertRaisesRegex(ValueError, 'vertically offset'):
            verify_design.check_graph(HISTORY.replace('0,32,0,0', '0,24,0,0'))

    def test_old_drag_header_height_fails(self):
        with self.assertRaisesRegex(ValueError, 'drag header'):
            verify_design.check_graph(HISTORY.replace('Height="32" PointerPressed', 'Height="24" PointerPressed'))


class PatchSequenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.a = self.root / 'layouts/example/patches/00-base.patch'
        self.b = self.a.with_name('60-integration.patch')
        self.a.parent.mkdir(parents=True)
        self.header = 'diff --git a/src/Views/Launcher.axaml b/src/Views/Launcher.axaml\n'
        self.a.write_text(self.header)
        self.b.write_text(self.header)
        self.relative = self.b.relative_to(self.root).as_posix()
        self.override = patch.object(layout, 'THEMES_DIR', self.root)
        self.override.start()

    def tearDown(self):
        self.override.stop()
        self.temp.cleanup()

    def test_explicit_revision_passes(self):
        profile = {'revisions': {self.relative: ['src/Views/Launcher.axaml']}}
        self.assertEqual(layout.validate_patch_sequence(profile, [self.a, self.b]), {'src/Views/Launcher.axaml'})

    def test_undeclared_overlap_fails(self):
        with self.assertRaises(layout.LayoutError):
            layout.validate_patch_sequence({}, [self.a, self.b])

    def test_reordering_revision_before_base_fails(self):
        profile = {'revisions': {self.relative: ['src/Views/Launcher.axaml']}}
        with self.assertRaises(layout.LayoutError):
            layout.validate_patch_sequence(profile, [self.b, self.a])

    def test_unknown_revision_file_fails(self):
        with self.assertRaises(layout.LayoutError):
            layout.validate_patch_sequence({'revisions': {'missing.patch': []}}, [self.a])

    def test_duplicate_entry_inside_one_patch_fails(self):
        self.a.write_text(self.header + self.header)
        with self.assertRaises(layout.LayoutError):
            layout.validate_patch_sequence({}, [self.a])

    def test_missing_declared_revision_target_fails(self):
        profile = {'revisions': {self.relative: ['src/Views/Launcher.axaml', 'src/Views/Absent.axaml']}}
        with self.assertRaises(layout.LayoutError):
            layout.validate_patch_sequence(profile, [self.a, self.b])


if __name__ == '__main__':
    unittest.main()
