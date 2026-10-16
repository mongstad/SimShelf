import React from "react";
import type { Run } from "./types";
export function CaptureSummary({ run }: { run: Run }) {
  const counts = run.capture_counts;
  const observed = counts
    ? Object.values(counts).reduce((a, b) => a + b, 0)
    : null;
  return (
    <div className="capture-summary">
      <p>
        <strong>Capture inspection: {run.capture_status}</strong>
      </p>
      <p>
        Inspected folder:{" "}
        <code>{run.capture_root || "Not recorded in this older run"}</code>
      </p>
      {counts ? (
        <>
          <p>
            {counts.copied || 0} copied · {counts.referenced || 0} referenced ·{" "}
            {counts.ignored || 0} ignored · {counts.skipped || 0} skipped ·{" "}
            {counts.unchanged || 0} unchanged
          </p>
          {observed === 0 && (
            <p className="text-amber">
              No eligible files observed in the capture folder. Expected outputs
              may be elsewhere or may not have been written.
            </p>
          )}
          {observed !== 0 && !(counts.copied || counts.referenced) && (
            <p>No new or changed files were retained by automatic capture.</p>
          )}
        </>
      ) : (
        <p>Capture counts are not available for this run.</p>
      )}
      <p className="muted">
        “Complete” means inspection finished without reported errors, not that
        all script outputs were preserved. Only copied files are backed up;
        references need the original files. Unchanged and ignored files are
        excluded. Later attachments are listed separately in Files.
      </p>
      {run.launch?.output_review?.targets.map((target, i) => (
        <p key={i}>
          <code>{target.resolved_path}</code> —{" "}
          {target.covered
            ? "Declared inside capture coverage at launch; check Files for actual retention."
            : target.reason}
        </p>
      ))}
    </div>
  );
}
