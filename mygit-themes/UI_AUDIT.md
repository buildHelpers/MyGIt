# MyGIt UI integration audit — 2026-11-06

The current implementation is **partial**, not a completed reproduction of all six approved mockups. Packaging overlays is not equivalent to implementing or visually validating the design.

## Corrections in this change

- Exactly one title-bar repository picker, using the original `OnOpenPagesCommandPalette` entry point and Ctrl/Cmd+P binding. Both routes open the same recent/search panel.
- Correct the workspace button tooltip.
- Remove the duplicated repository-section tab strip; preserve the left navigation and existing numeric shortcuts, without leaving an empty 44px row.
- Match the history graph offset and drag header to the 32px table header (previously 24px).
- Update working-copy resizing to reserve Diff, splitters and the right commit composer, rather than applying the old two-pane width formula.

The ordered `60-integration.patch` revises four UI paths declared explicitly in the manifest, and adds a resize correction for `WorkingCopy.axaml.cs`. Undeclared overlaps, wrong ordering and repeated patch files are rejected. Upstream `src/` stays untouched on the product branch.

## Remaining design work

| Surface | Current state and remaining gap |
|---|---|
| Home | Recent cards coexist with the upstream repository tree; not the full card-based mockup. Responsive sizing and repeated page/toolbar actions still need work. |
| Working copy | Three panes are wired, but compact-window layout, scrolling and composer controls have not been run or compared. |
| History | Density and split-view changes exist; detailed hierarchy and actual graph rendering are not visually validated. |
| Branches/worktrees | The new table/cards reuse some upstream operations; design action coverage, empty states, long paths and selection states remain to be checked. |
| Conflicts | Primarily a restyle of the existing three-way editor, not a complete recreation of the designed screen. |
| Preferences | Left categories still contain upstream forms, not the full card-based Appearance/AI design. |
| Application icon | Only a concept image and title-bar branch glyph exist; no new platform icon assets or installer integration have been committed. |

## Evidence and limitations

Executed locally: 14 new standard-library regression tests passed; Python syntax compilation passed. The integration patch was applied and reversed using Git against the exact retrieved Launcher XML blob `eb20f29cd19eb1645b91c1a6d7d6351ce48fdcc2` and retrieved source-range fixtures for the other four targets. The full corrected Launcher XML has one picker and one shortcut. Range fixtures are NOT an app checkout or runtime test.

Not executed: complete seven-patch assembly on a full checkout, .NET compilation, macOS launch, screenshot comparison. The container has no .NET SDK and cannot resolve GitHub for Git cloning; repository reads/writes used the GitHub connector. The tests validate guards and selected fixes, not visual completion.

On a clean checkout:

```bash
python3 -m unittest discover -s mygit-themes/tools -p 'test_*.py'
python3 mygit-themes/tools/theme.py check mygit-design
python3 mygit-themes/tools/theme.py build mygit-design --output ../MyGIt-Design-Fixed
```

Use a new output directory. Pulling the product branch does not rewrite an old generated worktree or an installed application. Keep the original six mockups as the target; generated design images are not application screenshots.
