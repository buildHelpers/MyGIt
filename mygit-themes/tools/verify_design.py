#!/usr/bin/env python3
"""Static checks of GENERATED UI, not proof of compilation or visual parity.

Usage: python3 mygit-themes/tools/verify_design.py ../MyGIt-Design
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

A = '{https://github.com/avaloniaui}'
X = '{http://schemas.microsoft.com/winfx/2006/xaml}'
VIEW_NAMES = (
    'Launcher', 'LauncherPage', 'Welcome', 'QuickRepositorySwitcher', 'Repository',
    'WorkingCopy', 'Histories', 'BranchesOverview', 'MergeConflictEditor', 'Conflict',
    'Preferences', 'RepositoryConfigure', 'StashesPage', 'DiffView', 'CommitDetail',
    'RepositoryToolbar',
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read(root: Path, path: str) -> str:
    return (root / path).read_text(encoding='utf-8-sig')


def check_navigation(markup: str, code: str) -> None:
    tree = ET.fromstring(markup)
    buttons = list(tree.iter(A + 'Button'))
    pickers = [b for b in buttons if b.get('Click') in (
        'OnOpenPagesCommandPalette', 'OnOpenRecentRepositories')]
    require(len(pickers) == 1, 'Expected one repository switcher, not overlapping old/new buttons')
    picker = pickers[0]
    require(picker.get('Click') == 'OnOpenPagesCommandPalette', 'Preserve the original picker entry point')
    shortcut = '{OnPlatform Ctrl+P, macOS=⌘+P}'
    require(picker.get('HotKey') == shortcut, 'The repository picker must keep Ctrl/Cmd+P')
    require(sum(b.get('HotKey') == shortcut for b in buttons) == 1, 'Duplicate Ctrl/Cmd+P binding')
    handler = re.search(r'private void OnOpenPagesCommandPalette\([^)]*\)\s*\{([^}]+)\}', code)
    require(handler is not None and 'OnOpenRecentRepositories(sender, e);' in handler.group(1),
            'Mouse and keyboard must reach the same repository panel')
    for event in ('OnShowWorkspaceHome', 'OnOpenWorkspaceMenu'):
        require(sum(b.get('Click') == event for b in buttons) == 1, f'Expected one {event} action')
    title = next(n for n in tree.iter(A + 'Grid') if n.get('ColumnDefinitions') and n.get('Grid.Row') == '0')
    columns = len(title.get('ColumnDefinitions').split(','))
    for child in title:
        column = int(child.get('Grid.Column', '0'))
        span = int(child.get('Grid.ColumnSpan', '1'))
        require(column + span <= columns, 'Orphaned title-bar grid column after removing duplicate action')


def check_graph(markup: str) -> None:
    tree = ET.fromstring(markup)
    listing = next(n for n in tree.iter() if n.tag.endswith('}HistoriesCommitList'))
    graph = next(n for n in tree.iter() if n.tag.endswith('}CommitGraph'))
    header = next(n for n in tree.iter(A + 'Border') if n.get('PointerPressed') == 'OnCommitListHeaderPointerPressed')
    height = float(listing.get('ColumnHeaderHeight'))
    require(float(header.get('Height')) == height, 'History drag header height disagrees with table header')
    require(float(graph.get('Margin').split(',')[1]) == height, 'History graph is vertically offset from rows')


def check_completed_screens(root: Path) -> None:
    home = ET.fromstring(read(root, 'src/Views/Welcome.axaml'))
    home_buttons = list(home.iter(A + 'Button'))
    require(any(b.get('Click') == 'OnCloneRepository' for b in home_buttons),
            'Dashboard is missing Clone action card')
    require(any(b.get('Click') == 'OnOpenLocalRepository' for b in home_buttons),
            'Dashboard is missing local repository action card')
    require(any(b.get('Command') == '{Binding AddRootNode}' for b in home_buttons),
            'Dashboard is missing create-group action card')
    require(any(n.get('HorizontalScrollBarVisibility') == 'Auto'
                for n in home.iter(A + 'ScrollViewer')),
            'Recent repository cards must scroll horizontally')

    branches = read(root, 'src/Views/BranchesOverview.axaml')
    repository = read(root, 'src/ViewModels/Repository.cs')
    branch_code = read(root, 'src/Views/BranchesOverview.axaml.cs')
    require('Text="{Binding BranchSearchText, Mode=TwoWay}"' in branches,
            'Branch search input is missing')
    require('ItemsSource="{Binding FilteredBranches, Mode=OneWay}"' in branches,
            'Branch list must bind to live search results')
    require('public bool HasFilteredBranches' in repository,
            'Branch empty result state has no view model')
    require('Click="OnOpenWorktree"' in branches and
            'void OnOpenWorktree(' in branch_code,
            'Worktree cards need an explicit Open action')
    require('Click="OnCheckoutBranch"' in branches and
            'void OnCheckoutBranch(' in branch_code,
            'Eligible local branches need explicit checkout action')

    conflict = ET.fromstring(read(root, 'src/Views/MergeConflictEditor.axaml'))
    editors = [n for n in conflict.iter(A + 'Grid') if
               n.get('Grid.Row') == '2' and
               n.get('ColumnDefinitions') == '*,*,*,22']
    require(len(editors) == 1, 'Merge editor must use three side-by-side content panes')
    positions = {child.get('Grid.Column') for child in editors[0] if child.tag == A + 'Border'}
    require({'0', '1', '2', '3'}.issubset(positions),
            'Ours / Result / Theirs / minimap are not in distinct columns')
    for name in ('OursPresenter', 'ResultPresenter', 'TheirsPresenter'):
        require(sum(n.get(X + 'Name') == name for n in conflict.iter()) == 1,
                f'Merge editor lost {name}')

    appearance = read(root, 'src/Views/Preferences.axaml')
    prefs_code = read(root, 'src/Views/Preferences.axaml.cs')
    for action in ('OnSelectMyGItLight', 'OnSelectMyGItDark', 'OnSelectSystemTheme'):
        require(appearance.count(f'Click="{action}"') == 1,
                f'Duplicate or missing appearance action: {action}')
        require(f'void {action}(' in prefs_code,
                f'Appearance action has no handler: {action}')

    # Icon resources are generated by the theme composer, not committed over
    # the upstream assets in the product branch.
    icons = {
        'src/App.ico': bytes((0, 0, 1, 0)),
        'build/resources/app/App.icns': b'icns',
        'build/resources/_common/icons/sourcegit.png': bytes((137, 80, 78, 71, 13, 10, 26, 10)),
    }
    for path, signature in icons.items():
        image = (root / path).read_bytes()
        require(image.startswith(signature), f'Generated icon has invalid signature: {path}')
        require(len(image) > 1024, f'Generated icon unexpectedly small: {path}')
    print('PASS completed-screen structure and platform icon signatures')


def verify_tree(root: Path) -> None:
    files = ['src/App.axaml', 'src/SourceGit.csproj', 'src/Resources/Styles.axaml', 'src/Resources/Themes.axaml']
    files += [f'src/Views/{name}.axaml' for name in VIEW_NAMES]
    locales = list((root / 'src/Resources/Locales').glob('*.axaml'))
    require(bool(locales), 'Missing locale resources')
    for path in files:
        ET.parse(root / path)
    for path in locales:
        ET.parse(path)
    print(f'PASS XML: {len(files) + len(locales)} files')

    check_navigation(read(root, 'src/Views/Launcher.axaml'), read(root, 'src/Views/Launcher.axaml.cs'))
    repository = ET.fromstring(read(root, 'src/Views/Repository.axaml'))
    navigation = [n for n in repository.iter(A + 'ListBox') if n.get('SelectedIndex') == '{Binding SelectedViewIndex, Mode=TwoWay}']
    require(len(navigation) == 1, 'Repository section navigation is duplicated')
    require('Auto,44,*' not in read(root, 'src/Views/Repository.axaml'), 'Removed navigation row still reserves height')
    check_graph(read(root, 'src/Views/Histories.axaml'))
    check_completed_screens(root)
    print('PASS single navigation entry, shared shortcut and history alignment')

    code = read(root, 'src/Views/WorkingCopy.axaml.cs')
    require('columns.Count != 5' in code and 'var reserved =' in code and 'Math.Clamp(' in code,
            'Working copy still uses the upstream two-column resize calculation')
    working = ET.fromstring(read(root, 'src/Views/WorkingCopy.axaml'))
    layout = next(n for n in working.iter(A + 'Grid') if n.get('SizeChanged') == 'OnMainLayoutSizeChanged')
    columns = layout.find(A + 'Grid.ColumnDefinitions')
    require(columns is not None and len(columns) == 5, 'Working-copy layout must reserve five columns')
    require('CommitMessageToolBox' in read(root, 'src/Views/WorkingCopy.axaml'), 'Commit composer missing')
    require('IsBranchesVisible' in read(root, 'src/ViewModels/Repository.cs'), 'Branch view not connected')
    require('TabStripPlacement="Left"' in read(root, 'src/Views/Preferences.axaml'), 'Settings category navigation missing')
    require('RecentRepositories' in read(root, 'src/Views/Welcome.axaml'), 'Recent home cards missing')

    keys = {n.get(X + 'Key') for n in ET.parse(root / 'src/Resources/Locales/en_US.axaml').getroot()}
    for name in VIEW_NAMES:
        text = read(root, f'src/Views/{name}.axaml')
        for key in re.findall(r'\{DynamicResource (Text\.[\w.]+)\}', text):
            require(key in keys, f'Unknown localized resource in {name}: {key}')
    quick_keys = ('Button', 'Title', 'Hint', 'Search', 'Recent', 'Open', 'NoResults', 'Keyboard')
    for path in locales:
        source = path.read_text(encoding='utf-8-sig')
        for key in quick_keys:
            require(source.count(f'x:Key="Text.QuickRepo.{key}"') == 1, f'Missing/duplicate locale key {path}: {key}')
    for view, event in (
        ('Welcome', 'OnRecentRepositoryTapped'), ('BranchesOverview', 'OnBranchDoubleTapped'),
        ('BranchesOverview', 'OnWorktreeDoubleTapped'), ('QuickRepositorySwitcher', 'OnRepositoryTapped'),
    ):
        require(event in read(root, f'src/Views/{view}.axaml'), f'Missing event binding: {view}.{event}')
        require(re.search(rf'\bvoid\s+{event}\s*\(', read(root, f'src/Views/{view}.axaml.cs')) is not None,
                f'Missing event handler: {view}.{event}')
    print('PASS layout wiring and localization references; compilation and GUI comparison still required')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        verify_tree(args.root.expanduser().resolve())
        return 0
    except (OSError, ValueError, ET.ParseError, StopIteration) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
