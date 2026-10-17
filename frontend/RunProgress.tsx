import React from "react";
import type { Run } from "./types";

export function RunProgress({ run }: { run: Run }) {
  const report = run.progress;
  if (!report && run.status !== "running" && !run.progress_error) return null;
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
  return (
    <section className="run-progress" aria-label="Simulation progress">
      <div className="progress-heading">
        <strong>
          {report
            ? "Last reported progress"
            : run.status === "running"
              ? "Running · progress not reported"
              : "Progress unavailable"}
        </strong>
        {percent !== null && <span>{percent}%</span>}
      </div>
      {known && (
        <progress
          aria-label="Last reported simulation progress"
          value={report!.current!}
          max={report!.total!}
        />
      )}
      {report && (
        <>
          {report.stage && <div className="progress-stage">{report.stage}</div>}
          <div className="muted">
            {known ? `${report.current} / ${report.total}` : "Total unknown"}
            {report.current !== null &&
              !known &&
              ` · ${report.current} reported`}
            {" · "}
            {report.source === "structured"
              ? "Reported by simulation API"
              : `Interpreted from ${report.source.replace("text:", "")}`}
            {" · "}
            {new Date(report.reported_at).toLocaleString()}
          </div>
          <small className="muted">
            {run.status === "running"
              ? known
                ? "The run is still running. Reports may be infrequent; 100% does not mean it has finished."
                : "The run is still running. Reports may be infrequent."
              : `Run ${run.status}. This is its last report, not a completion guarantee.`}
          </small>
        </>
      )}
      {run.progress_error && (
        <p role="alert">
          Progress could not be saved completely: {run.progress_error}
        </p>
      )}
    </section>
  );
}
