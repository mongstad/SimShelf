# Deliberate run removal

Issue #15 design: removal hard-deletes selected run rows, metrics, attachments and
annotation history in one transaction, retaining a minimal deletion audit entry
(run ID, simulation ID, version, start/deletion times and source identifiers).
The audit prevents old journal events from resurrecting removed runs. It is not
an undo copy. Source folders, original outputs, external references and Git are
never deletion targets. Existing backup archives retain their original data.

Only finalized completed, failed or interrupted records are eligible. A batch is
all-or-nothing; stale/unknown IDs or any running record reject the entire request.
Already removed IDs are idempotent. Final capture happens before final status.
The confirmation identifies exact IDs; an annotation change cannot change targets.

A workspace lock coordinates removal with source preparation/start, attachments,
journal writes/replay and backups across threads and Linux processes. Deletion
commits an explicit queue of managed relative filenames before filesystem cleanup.
Cleanup checks current live source/artifact references under the same lock, never
follows symlinks, and retries failures during recovery. It does not sweep arbitrary
workspace files. A crash after commit cannot restore records or lose the queue.
Pending journal failures block deletion/reclamation until resolved.

Surviving records' baseline IDs and change classifications remain unchanged.
If their baseline run is removed, its source snapshot is retained for comparison
and labeled as a removed baseline. Once no surviving run needs it, it becomes
eligible for cleanup. Future runs use the earliest surviving run as their baseline;
with no surviving runs they establish a new baseline. Version counts, favorites
and comparison selection include surviving records only.

The first explicit run deletion marks a schema-1 workspace as version 2 in that same
transaction. Opening/recording/backing up schema-1 libraries remains supported;
there is no startup data migration. Older SimShelf versions reject version 2 on
open. Stop other older application/recorder versions before using deletion.
Fresh backups retain the minimal audit but omit removed payloads and cleanup tasks;
restoring an old backup can bring back the old records. SQLite/WAL free pages,
filesystem recovery and old backups mean this is not secure erasure.

This design is Linux/local-filesystem only. Locking is bounded to data operations,
not a simulation's lifetime; long captures or backups can delay removal. No
individual screenshot removal, simulation removal, retention policy or automatic
age/failure deletion is introduced.

Libraries already on schema 3 after [screenshot deletion](SCREENSHOT_DELETION.md)
remain on schema 3; run removal never downgrades their replay protections.
