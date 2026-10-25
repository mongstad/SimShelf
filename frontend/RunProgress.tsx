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
  // Use the run's frozen adapter only for text reports: structured input wins
  // over text parsing and has no declared unit. Never infer percent from total=100.
  const textSource = report?.source === "text:stdout" || report?.source === "text:stderr";
  const textMode = run.progress_mode === "auto" ? report?.text_mode : run.progress_mode;
  const percentage = textSource && textMode === "percent";
  const discrete = !percentage &&
    (report?.source === "structured" || (textSource && textMode === "step")) &&
    Number.isInteger(report?.total) &&
    (report?.current == null || Number.isInteger(report.current));
  const unit = discrete ? "steps" : "units";
  const completed = run.status === "completed";
  // Completion is a display projection only; never overwrite the stored report.
  const displayedPercent = completed ? 100 : known && percentage ? report!.current : percent;
  const displayedCurrent = completed ? report?.total : report?.current;
  const showCounts = !percentage && (completed ? validTotal : known);
  const formatCount = (value: number) => value.toLocaleString("en-US", { maximumSignificantDigits: 21 });
  return (
    <section className="run-progress" aria-label="Simulation progress">
      <div className="progress-heading">
        <strong>
          {completed || known ? "Progress" : "Progress unavailable"}
        </strong>
        {displayedPercent != null && <span>{displayedPercent}%</span>}
      </div>
      {(completed || known) && (
        <progress
          aria-label={completed ? "Successful process completion" : "Simulation progress"}
          aria-valuetext={completed
            ? showCounts
              ? `100% process completion; ${formatCount(report!.total!)} of ${formatCount(report!.total!)} ${unit} displayed from the stored total, not a measured progress report`
              : "100% process completion; not a measured progress report"
            : percentage
              ? `${formatCount(report!.current!)}% reported progress`
              : `${percent}% reported progress; ${formatCount(report!.current!)} of ${formatCount(report!.total!)} ${unit}`}
          value={completed ? 100 : report!.current!}
          max={completed ? 100 : report!.total!}
        />
      )}
      {showCounts && (
        <div className="muted">
          {formatCount(displayedCurrent!)}
          {" / "}
          {formatCount(report!.total!)} {unit}
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
