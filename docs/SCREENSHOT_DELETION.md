# Delete a screenshot from a previous run

Open the run's **Screenshots** tab, choose **Delete screenshot** under the image,
and review the image name and run name. IDs remain internal deletion targets.
Cancel has initial focus; Escape also cancels. The restrained red button and trash icon identify the destructive
action. Confirmation removes the attachment from this library permanently,
not just from the current view. The gallery/count update immediately; when the
cover is removed the first remaining saved image becomes the displayed cover.

Only manually attached managed PNG/JPEG/WebP/GIF copies on completed, failed or
interrupted runs are eligible, after output capture finishes. Browser uploads and
explicit Python attachments record `automatic=false`. Automatically captured
outputs and older attachments without explicit ownership metadata are protected.
External references remain in Files; this action cannot remove their references
or original files. The disabled control explains protected gallery images.
Missing managed image bytes do not prevent removal of the attachment record.

Original images, source projects, snapshots, captured outputs, logs, measurements,
other attachments and run execution records remain intact. When another attachment
or retained source snapshot uses the same content hash, only the selected reference
is removed and the shared bytes stay. The last eligible reference's removal can
reclaim the blob once no retained source/artifact references it.

There is no undo or secure-erasure guarantee. Back up first if needed. Existing
backups retain old contents; restore into a separate library to recover a copy.
Fresh backups omit deleted image payloads unless another retained reference needs
them, but include the deletion audit and original attachment metadata. Historical
journal/annotation records and SQLite/WAL free pages may still contain metadata.

## Storage and compatibility design

The owner explicitly authorized schema 3 for issue #24 on 2026-10-17. Opening,
recording and backing up schema-1/2 libraries does not migrate them. The first
successful, explicitly confirmed screenshot deletion atomically marks schema 3.
The dialog reads the current library format on every opening and warns about
compatibility only for schema 1 or 2. Once schema 3 is in use, later confirmations
omit this warning. Delete stays disabled if that check is pending or fails.
Older builds cannot reopen that library. Stop older servers/recorders first; an
already-open older process cannot be made safe by a newer process's check. Schema
3 backups require a schema-3-capable build. Later whole-run removal never downgrades
the schema. No scientific version, source snapshot or completed run row is changed.

The database is authoritative. One transaction removes the selected artifacts row,
adds a `deleted_screenshot:<id>` metadata tombstone holding its run ID, timestamp
and original attachment metadata, appends a `screenshot_deleted` annotation-history
entry, and queues the strictly hash-derived blob path for cleanup. Original events
and caption history remain; replay ignores attachment/caption events for tombstoned
IDs. The recorded historical cover annotation stays unchanged; gallery/list display
uses a surviving image. Duplicate requests for the same run/ID are idempotent.

Deletion uses the existing workspace lock across threads/Linux processes, shared
with attachment publication, source capture/start, journal replay, backups and file
reclamation. Pending journal errors block deletion. Cleanup protects current
artifact blobs and source snapshots, including retained deleted baselines. Unlink
opens directory descriptors without following symlinks and accepts only the managed
blob path derived from the validated SHA-256 ID. Neither the API nor cleanup accepts
an original path from the client. The API checks the selected run/attachment pair,
explicit confirmation, local host, same origin and session token.

After a committed removal, file-cleanup errors mean the gallery entry is gone but
bytes may remain; the success message reports this distinction. Periodic recovery
or `simshelf doctor` retries the persisted queue. Fix permissions or investigate an
unexpected symlink without deleting original files. Before-commit permission/DB
failures preserve the attachment and return an actionable error. A lost response can
be checked by refreshing or safely retrying the same IDs. Long captures/backups can
delay deletion. Local adversarial writers bypassing SimShelf's lock, network-file-
system semantics and physical disk failure are not certified by this design.
