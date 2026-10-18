# Remove a registered simulation

[All guides](README.md) · [Run removal](RUN_REMOVAL.md)

Select a simulation, open the **Simulation settings** cogwheel at the upper-right
of its overview, then choose **Remove simulation…**. Settings also contains
**Change source location…**, which opens the separate relocation review. A missing
source keeps a visible **Locate source folder…** recovery action on the overview.
Review the simulation name and ID, run count, referenced snapshots, images,
annotation history, measurements, managed copies, external references and Git
archive associations. **Cancel** is initially focused. Nothing is removed until
you type the exact current name (including case, spaces and punctuation) and
choose **Remove simulation**. Enter in the name field does not submit the action.

Removal unregisters the simulation and removes all its runs from this library,
including notes, measurements, logs and unshared managed files. The portal returns
to **All simulations**. There is no in-place undo: use **Back up workspace** first
if you may need the records, and restore into a separate empty workspace to recover
them. Older backups retain their contents.

Original source folders, Python files, source Git repositories, output folders
and reference-only scientific files are never deleted or modified. Managed copies
and source snapshots still needed by surviving runs remain. Library associations
to the shared Git archive are removed, but existing archive commits and bytes
remain untouched, even if the archive is unavailable. This is not an archive purge
or secure erase; disk space in that archive may remain occupied.

Running or finalizing portal, terminal or editor runs block removal. Stop them and
wait for capture to finish, then reopen the review. A changed name, run or related
record also invalidates the review: reopen it and confirm the current state.
Do not try to bypass a journal or cleanup error reported by the operation.

Simulation removal requires an existing schema-2, schema-3 or schema-4 library.
It refuses schema-1 libraries, even for zero-run simulations, and never upgrades
any library. There is no migration action in this workflow.

If the response is lost, refresh to inspect the library. Retrying the exact same
confirmation is safe. Once sent, closing the dialog cannot cancel the request.
Database removal is atomic; managed-file cleanup happens afterward and is retried
by workspace recovery if interrupted. A cleanup warning means records were removed
but some eligible managed files remain pending cleanup. Minimal deletion records
prevent old journal events from restoring deleted runs. Registering the same
source again creates a new simulation ID and does not reattach the removed history.
