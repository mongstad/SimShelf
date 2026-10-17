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
  const completed = run.status === "completed";
  return (
    <section className="run-progress" aria-label="Simulation progress">
      <div className="progress-heading">
        <strong>
          {completed || known ? "Progress" : "Progress unavailable"}
        </strong>
        {!completed && percent !== null && <span>{percent}%</span>}
      </div>
      {(completed || known) && (
        <progress
          aria-label={completed ? "Successful process completion" : "Simulation progress"}
          aria-valuetext={completed
            ? known
              ? `Process completed; last reported progress ${percent}%, ${report!.current!.toLocaleString("en-US", { maximumFractionDigits: 12 })} of ${report!.total!.toLocaleString("en-US", { maximumFractionDigits: 12 })} steps`
              : "Process completed; no reported progress available"
            : undefined}
          value={completed ? 100 : report!.current!}
          max={completed ? 100 : report!.total!}
        />
      )}
      {completed && (
        <div className="progress-heading">
          <strong>{known ? "Last reported progress" : "Progress unavailable"}</strong>
          {percent !== null && <span>{percent}%</span>}
        </div>
      )}
      {known && (
        <div className="muted">
          {report!.current!.toLocaleString("en-US", { maximumFractionDigits: 12 })}
          {" / "}
          {report!.total!.toLocaleString("en-US", { maximumFractionDigits: 12 })} steps
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
