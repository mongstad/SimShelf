import React from "react";
import type { Run } from "./types";

export function RunProgress({ run }: { run: Run }) {
  const report = run.progress;
  const validTotal = typeof report?.total === "number" && Number.isFinite(report.total) && report.total > 0;
  const known =
    report &&
    typeof report.current === "number" &&
    Number.isFinite(report.current) &&
    validTotal &&
    report.current >= 0 &&
    report.current <= report.total!;
  const percent = known
    ? report!.current! === report!.total
      ? 100
      : Math.min(
          99.9,
          Math.round((report!.current! / report!.total!) * 1000) / 10,
        )
    : null;
  const completed = run.status === "completed";
  // Completion is a display projection only; never overwrite the stored report.
  const displayedPercent = completed ? 100 : percent;
  const displayedCurrent = completed ? report?.total : report?.current;
  const showCounts = completed ? validTotal : known;
  const formatCount = (value: number) => value.toLocaleString("en-US", { maximumFractionDigits: 12 });
  return (
    <section className="run-progress" aria-label="Simulation progress">
      <div className="progress-heading">
        <strong>
          {completed || known ? "Progress" : "Progress unavailable"}
        </strong>
        {displayedPercent !== null && <span>{displayedPercent}%</span>}
      </div>
      {(completed || known) && (
        <progress
          aria-label={completed ? "Successful process completion" : "Simulation progress"}
          aria-valuetext={completed
            ? validTotal
              ? `100% process completion; ${formatCount(report!.total!)} of ${formatCount(report!.total!)} steps displayed from the stored total, not a measured progress report`
              : "100% process completion; no valid step total available, not a measured progress report"
            : undefined}
          value={completed ? 100 : report!.current!}
          max={completed ? 100 : report!.total!}
        />
      )}
      {showCounts && (
        <div className="muted">
          {formatCount(displayedCurrent!)}
          {" / "}
          {formatCount(report!.total!)} steps
        </div>
      )}
      {report?.stage && <div className="progress-stage">{report.stage}</div>}
      {run.progress_error && (
        <p role="alert">
          Progress could not be saved completely: {run.progress_error}
        </p>
      )}
    </section>
  );
}
