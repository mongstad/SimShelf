# Legacy Git file-selection preferences

The current UI uses [Preservation settings](GIT_ARCHIVE.md) to review capture and
Git inclusion together. Source Git remains an independent read-only provenance
connection. The former Manage Git files and shallow future-output controls no
longer configure new policies in the UI.

Existing file/folder/extension preferences, `.gitignore` edits and legacy archive
consent are retained. Legacy API clients keep the bounded inventory, exact review,
location binding and explicit ignore-write behavior; these preferences do not
silently become recursive format-2 consent. An adopted policy refuses legacy
re-enablement. Explicit new-policy adoption preserves earlier consent as metadata
and leaves historical plans, commits and scientific records unchanged.

Source inventories still prune the configured capture directory before traversal,
including nested generated directories. They inspect at most 1,000 entries and
bounded ignore text, without using filenames to guess scientific ownership.
Other source paths remain visible regardless of snapshot inclusion; the combined
review distinguishes what the actual snapshot rules capture. If an inventory is
too large, review the configured capture parent or register a smaller source
folder; do not remove research data to bypass a warning.

The [architecture](LIBRARY_PRESERVATION_DESIGN.md) describes compatibility, policy
binding and the new recursive selection. Historical validation reports retain
their original evidence and interface wording.
