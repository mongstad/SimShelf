import React from "react";
import type { Run } from "./types";

type Preservation = { state?: string; connection?: string } | null;
export function overviewWarnings(
  run: Run,
  preservation: Preservation,
  loading = false,
) {
  const warnings: { text: string; pending: boolean }[] = [];
  if (run.capture_status === "pending") {
    warnings.push({
      text:
        run.status === "running"
          ? run.stop_requested
            ? "Stopping; workspace capture is pending."
            : "Workspace capture is pending."
          : "Execution ended; workspace capture is pending.",
      pending: true,
    });
  } else if (run.capture_status !== "complete") {
    warnings.push({
      text:
        run.capture_status === "partial" || run.capture_status === "incomplete"
          ? `Workspace capture is ${run.capture_status}.`
          : "Workspace capture status is unavailable.",
      pending: false,
    });
  } else if (run.capture_errors?.length) {
    warnings.push({
      text: "Workspace capture reported errors.",
      pending: false,
    });
  } else if ((run.capture_counts?.skipped || 0) > 0) {
    warnings.push({
      text: "Files were skipped during workspace capture.",
      pending: false,
    });
  }
  if (
    run.capture_status === "complete" &&
    run.capture_counts &&
    Object.values(run.capture_counts).every((count) => count === 0)
  ) {
    warnings.push({
      text: "No eligible files were observed during capture.",
      pending: false,
    });
  }
  if (run.launch?.output_review?.targets.some((target) => !target.covered)) {
    warnings.push({
      text: "Declared outputs extend outside capture coverage.",
      pending: false,
    });
  }
  if (
    run.artifacts?.some(
      (file) =>
        file.availability === "missing" ||
        file.availability === "another-computer",
    )
  ) {
    warnings.push({ text: "Recorded files are unavailable.", pending: false });
  }
  if (run.artifacts?.some((file) => file.availability === "changed")) {
    warnings.push({
      text: "Referenced files have changed since recording.",
      pending: false,
    });
  }
  if (loading)
    warnings.push({ text: "Checking Git preservation…", pending: true });
  else if (preservation?.state === "verified") {
    if (preservation.connection !== "connected")
      warnings.push({
        text: "Git preservation repository is unavailable.",
        pending: false,
      });
  } else if (preservation?.state !== "not_enabled") {
    const state = preservation?.state;
    warnings.push({
      text:
        state === "pending"
          ? "Git preservation is pending."
          : state === "partial" || state === "failed"
            ? `Git preservation is ${state}.`
            : "Git preservation status is unavailable.",
      pending: state === "pending",
    });
  }
  return warnings;
}
export function RunOverviewWarnings({
  run,
  preservation,
  loading = false,
  openFiles,
}: {
  run: Run;
  preservation: Preservation;
  loading?: boolean;
  openFiles: () => void;
}) {
  const warnings = overviewWarnings(run, preservation, loading);
  if (!warnings.length) return null;
  return (
    <div
      className="run-overview-warnings"
      aria-label="Capture and preservation notices"
    >
      {warnings.map((warning) => (
        <p key={warning.text} role={warning.pending ? "status" : "alert"}>
          <span>{warning.text}</span>{" "}
          <button className="text-button" onClick={openFiles}>
            View details in Files
          </button>
        </p>
      ))}
    </div>
  );
}
