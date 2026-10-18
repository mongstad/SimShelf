# Issue #52 / PR #81 — title-adjacent settings

Owner feedback 6255327059 moves the existing cogwheel directly after the simulation
heading. The title row uses a 14 px gap and vertical centering; the icon does not
shrink, while the heading can wrap even unbroken names. The former absolute
far-right position and reserved corner padding are removed. Launch controls,
settings workflows, missing-source recovery and all backend behavior are unchanged.
Application version remains 0.1.0.27. Prior review evidence is preserved.

## Focused validation

- TypeScript, bundled frontend build, existing settings/removal frontend checks,
  diff check and accepted-main version gate passed.
- External sdist/wheel-from-sdist and direct wheel built successfully; wheel
  contents matched. Installed offline API/static/version smoke passed without
  Git/Node on PATH. Artifacts are under `/tmp/simshelf-52-title-review`.
- Browser fixture used new disposable sources and workspace on port 8881; no owner
  data was used. Served the rebuilt checkout assets, not a published release.
- At 1440×900, “Vacuum Collapse Recirculator” and the icon have a measured 14 px
  gap and identical vertical centers. Screenshot visually confirms launch controls
  remain independent at the right.
- At 390×844, a long multi-word title and a 116-character unbroken title wrap
  without overlapping the icon. Multi-word title row client/scroll widths both
  measured 343 px; gap 14 px and vertical center difference 0.
- At narrow width, DOM geometry checks in Light, Dark, Onyx, Slate and Linen all
  found 14 px gap, zero center offset and no title-row horizontal overflow.
  Visual inspection covered System dark and Linen; this was not a full visual
  theme matrix or physical-device test.
- Enter on the cogwheel opens the same dialog with Cancel focused and both actions.
  Escape returns focus to the cogwheel. Missing-source Locate recovery remains
  visible. Change source location opens its existing path-entry review, and Cancel
  returns focus to the cogwheel. No relocation or deletion was committed.

No backend change or repeated backend suite was needed for this DOM/CSS placement
revision. No screen-reader, Windows/macOS or physical touch testing. Owner should
review title wrapping and icon placement with their actual simulation names before
merge. Issue #82 remains excluded; no merge or release performed.
