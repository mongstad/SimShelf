import React from "react";
import type { Run } from "./types";

export function SourceBadge({ run }: { run: Run }) {
  return run.entrypoint_warning?.warn ? (
    <span className="source-note changed">Captured source changed within version</span>
  ) : run.source_change === "text-only" ? (
    <span className="source-note">Comments / formatting</span>
  ) : null;
}
