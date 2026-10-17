export type OutputMapping = {
  argument_index: number | null;
  value: string;
  kind: "file" | "directory";
  format: "token" | "equals";
};
export type OutputReview = {
  output_path: string;
  requires_acknowledgement: boolean;
  targets: (OutputMapping & {
    resolved_path: string;
    covered: boolean;
    reason: string;
    suggested_argument: string | null;
  })[];
};
export type Config = {
  source_include: string[];
  source_exclude: string[];
  output_dir: string;
  max_file_mb: number;
  max_run_mb: number;
  rules: { pattern: string; action: "copy" | "reference" | "ignore" }[];
};
export type ExecutionSettings = {
  output_mappings?: OutputMapping[];
  interpreter: string;
  cwd: string;
  arguments: string[];
  output_dir: string;
};
export type Simulation = {
  execution?: ExecutionSettings;
  id: string;
  name: string;
  description: string;
  root: string;
  entrypoint: string | null;
  version_file: string | null;
  config: Config;
  run_count: number;
  available: boolean;
  last_run: string | null;
};
export type Artifact = {
  id: string;
  name: string;
  size: number;
  policy: string;
  media_type: string;
  availability: string;
  caption: string;
  original_path?: string;
  reason?: string;
};
export type Measurement = {
  name: string;
  value: number;
  step?: number;
  sim_time?: number;
  unit?: string;
};
export type Run = {
  launch?: {
    kind: string;
    output_review?: OutputReview;
    outputs_acknowledged?: boolean;
  };
  capture_root?: string;
  can_stop?: boolean;
  stop_requested?: boolean;
  id: string;
  simulation_id: string;
  name: string;
  status: string;
  version: string;
  source_change: string;
  snapshot_id: string;
  structure_id: string;
  started_at: string;
  ended_at: string | null;
  duration: number | null;
  command: string[];
  cwd: string;
  parameters: Record<string, unknown>;
  parameter_sources: Record<string, string>;
  notes: string;
  tags: string[];
  version_note: string;
  baseline_run_id: string;
  baseline_deleted?: boolean;
  cover_id?: string | null;
  image_count?: number;
  exit_code: number | null;
  error?: string | null;
  capture_status: string;
  capture_errors: string[];
  capture_counts?: Record<string, number>;
  source_warnings: string[];
  git: { commit: string | null; branch: string | null; dirty: boolean | null };
  environment: {
    python: string;
    executable: string;
    platform: string;
    source: string;
    packages: { name: string; version: string }[];
  };
  artifacts?: Artifact[];
  metrics?: Measurement[];
  metric_count?: number;
  snapshot?: { files: { path: string; size: number; blob: string }[] };
  annotation_history?: Record<string, unknown>[];
};
export type Version = {
  version: string;
  run_count: number;
  snapshots: number;
  structures: number;
  latest: string;
  changed: number;
};
export type CapturePreview = {
  files: { path: string; size: number; action: string; reason?: string }[];
  total_files: number;
  copy_bytes: number;
  errors: string[];
  truncated: boolean;
  counts: Record<string, number>;
};
