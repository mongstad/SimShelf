import React from "react";
import type { Run } from "./types";

export function RunProgress({ run }: { run: Run }) {
  const report = run.progress;
  const known =
    report &&
    typeof report.current === "number" &&
    Number.isFinite(report.current) &&
    typeof report.total === "number" &&
    Number.isFinite(report.total) &&
    report.total > 0 &&
    report.current >= 0 &&
    report.current <= report.total;
  const percent = known
    ? report!.current! === report!.total
      ? 100
      : Math.min(
          99.9,
          Math.round((report!.current! / report!.total!) * 1000) / 10,
        )
    : null;
  const completedBelowTotal =
    known && run.status === "completed" && report!.current! < report!.total!;
  return (
    <section className="run-progress" aria-label="Simulation progress">
      <div className="progress-heading">
        <strong>
          {known
            ? completedBelowTotal ? "Last reported progress" : "Progress"
            : "Progress unavailable"}
        </strong>
        {percent !== null && <span>{percent}%</span>}
      </div>
      {known && (
        <progress
          aria-label={completedBelowTotal ? "Last reported simulation progress" : "Simulation progress"}
          value={report!.current!}
          max={report!.total!}
        />
      )}
      {known && (
        <div className="muted">
          {report!.current!.toLocaleString("en-US", { maximumFractionDigits: 12 })}
          {" / "}
          {report!.total!.toLocaleString("en-US", { maximumFractionDigits: 12 })} steps
        </div>
      )}
      {report?.stage && <div className="progress-stage">{report.stage}</div>}
      {completedBelowTotal && <small className="muted">Process completed successfully.</small>}
      {run.progress_error && (
        <p role="alert">
          Progress could not be saved completely: {run.progress_error}
        </p>
      )}
    </section>
  );
}
