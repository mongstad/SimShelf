from __future__ import annotations

import json
import os
import socket
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from .common import atomic_write, contained, default_workspace, json_text, now, process_alive, slugify
from .config import read_project, validate_config
from .source import blob_path, read_snapshot
from .workspace_lock import locked_store
from .removal import deleted_run, cleanup_removed, remove_runs
from .screenshots import deleted_screenshot, deletion_reason

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS simulations (id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, simulation_id TEXT NOT NULL, status TEXT NOT NULL,
    started_at TEXT NOT NULL, version TEXT NOT NULL, data TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS runs_simulation ON runs(simulation_id, started_at);
CREATE TABLE IF NOT EXISTS artifacts (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, data TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS artifacts_run ON artifacts(run_id);
CREATE TABLE IF NOT EXISTS metrics (event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, data TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS metrics_run ON metrics(run_id);
CREATE TABLE IF NOT EXISTS annotations (event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS applied_events (id TEXT PRIMARY KEY);
"""


class Store:
    def __init__(self, workspace: str | Path | None = None):
        self.path = Path(workspace).expanduser().resolve() if workspace else default_workspace()
        self.path.mkdir(parents=True, exist_ok=True)
        self.db = self.path / "simshelf.sqlite3"
        with self.connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)
            row = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
            if row and row[0] not in {"1", "2", "3", "4"}:
                raise ValueError("This workspace uses a newer database schema. Upgrade SimShelf.")
            conn.execute("INSERT OR IGNORE INTO metadata VALUES ('schema_version', '1')")
            conn.execute("INSERT OR IGNORE INTO metadata VALUES ('workspace_id', ?)", (uuid.uuid4().hex,))

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.db, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=FULL")
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    @locked_store
    def add_simulation(self, root, name=None, entrypoint=None, version_file=None, config=None) -> dict:
        root = Path(root).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("Simulation folder does not exist")
        if root == self.path or root.is_relative_to(self.path):
            raise ValueError("Keep simulation source outside the managed workspace folder")
        project = read_project(root)
        name = (name or project.get("name") or root.name).strip()
        if not name or len(name) > 160:
            raise ValueError("Simulation name must contain 1–160 characters")
        entrypoint = entrypoint or project.get("entrypoint")
        if not entrypoint:
            candidates = sorted(p.name for p in root.glob("*.py"))
            entrypoint = candidates[0] if len(candidates) == 1 else None
        if entrypoint and not contained(root, entrypoint).is_file():
            raise ValueError("Entry file does not exist inside the simulation folder")
        version_file = version_file or project.get("version_file") or (entrypoint if entrypoint and entrypoint.endswith(".py") else None)
        if version_file and not contained(root, version_file).is_file():
            raise ValueError("Version file does not exist inside the simulation folder")
        config = validate_config(config if config is not None else project.get("config", {}))
        contained(root, config["output_dir"])
        with self.connection() as conn:
            for row in conn.execute("SELECT data FROM simulations"):
                existing = json.loads(row[0])
                if existing["root"] == str(root):
                    return existing
            ident = slugify(name)
            while conn.execute("SELECT 1 FROM simulations WHERE id=?", (ident,)).fetchone() or conn.execute("SELECT 1 FROM metadata WHERE key=?", ("deleted_simulation:" + ident,)).fetchone():
                ident += "-" + uuid.uuid4().hex[:6]
            data = {"id": ident, "name": name, "root": str(root), "entrypoint": entrypoint, "version_file": version_file, "config": config, "created_at": now(), "description": project.get("description", "")}
            conn.execute("INSERT INTO simulations VALUES (?,?)", (ident, json_text(data)))
        return data

    def simulations(self) -> list[dict]:
        from .simulation_activity import has_active_runs
        with self.connection() as conn:
            conn.execute("BEGIN")  # One read snapshot for counts and activity.
            result = [json.loads(row[0]) for row in conn.execute("SELECT data FROM simulations ORDER BY id")]
            for sim in result:
                sim["run_count"] = conn.execute("SELECT count(*) FROM runs WHERE simulation_id=?", (sim["id"],)).fetchone()[0]
                sim["last_run"] = conn.execute("SELECT max(started_at) FROM runs WHERE simulation_id=?", (sim["id"],)).fetchone()[0]
                sim["available"] = Path(sim["root"]).is_dir()
                sim["administration_active"] = has_active_runs(conn, sim["id"])
            return result

    def simulation(self, ident: str) -> dict:
        with self.connection() as conn:
            row = conn.execute("SELECT data FROM simulations WHERE id=?", (ident,)).fetchone()
        if not row:
            raise ValueError(f"Unknown simulation '{ident}'. Register its folder first with simshelf add.")
        return json.loads(row[0])

    @locked_store
    def update_simulation(self, ident: str, *, config=None, name=None, description=None, execution=None, entrypoint=None) -> dict:
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT data FROM simulations WHERE id=?", (ident,)).fetchone()
            if not row:
                raise ValueError("Simulation not found")
            data = json.loads(row[0])
            if config is not None:
                data["config"] = validate_config(config)
                contained(Path(data["root"]), data["config"]["output_dir"])
            if entrypoint is not None:
                if not isinstance(entrypoint, str) or Path(entrypoint).is_absolute() or Path(entrypoint).suffix != ".py" or not contained(Path(data["root"]), entrypoint).is_file():
                    raise ValueError("Choose an existing Python entry file relative to the registered source folder")
                data["entrypoint"] = entrypoint
            if execution is not None:
                from .portal import execution_settings
                plan = execution_settings(data, execution)
                data["execution"] = plan["settings"]
                metadata = plan["parameter_metadata"]
                if metadata["decision"]["mode"] == "typed" and metadata["provenance"]:
                    data["parameter_provenance"] = metadata["provenance"]
            if name is not None:
                if not name.strip() or len(name) > 160:
                    raise ValueError("Name must contain 1–160 characters")
                data["name"] = name.strip()
            if description is not None:
                data["description"] = description[:10000]
            conn.execute("UPDATE simulations SET data=? WHERE id=?", (json_text(data), ident))
        return data

    @locked_store
    def emit(self, run_id: str, kind: str, data: dict) -> str:
        if not run_id or any(c not in "0123456789abcdef" for c in run_id) or len(run_id) != 32:
            raise ValueError("Invalid run identifier")
        with self.connection() as conn:
            if deleted_run(conn, run_id):
                raise ValueError("Run was deliberately removed")
        event_id = f"{time.time_ns():020d}-{uuid.uuid4().hex}"
        event = {"id": event_id, "run_id": run_id, "kind": kind, "at": now(), "data": data}
        file = self.path / "journal" / run_id / (event_id + ".json")
        atomic_write(file, json_text(event).encode())
        try:
            self.apply(event)
        except ValueError:
            # Invalid events must never become valid later during journal replay.
            file.unlink(missing_ok=True)
            raise
        return event_id

    @locked_store
    def apply(self, event: dict) -> None:
        progress_error = None
        if event["kind"] == "finish":
            from .progress import recover_progress
            try:
                recover_progress(self, event["run_id"])
            except (ValueError, OSError, sqlite3.Error, KeyError, TypeError) as exc:
                progress_error = f"Progress recovery failed: {exc}"
        with self.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if conn.execute("SELECT 1 FROM applied_events WHERE id=?", (event["id"],)).fetchone():
                return
            run_id, kind, data = event["run_id"], event["kind"], event["data"]
            if deleted_run(conn, run_id):
                return  # Historical or delayed events must never resurrect removed runs.
            if kind == "start":
                if not conn.execute("SELECT 1 FROM simulations WHERE id=?", (data["simulation_id"],)).fetchone():
                    raise ValueError("Simulation was removed or is not registered")
                data = dict(data)
                for active in conn.execute("SELECT data FROM runs WHERE status='running'"):
                    existing = json.loads(active[0])
                    other_root = existing.get("capture_root")
                    if not other_root:
                        sim_row = conn.execute("SELECT data FROM simulations WHERE id=?", (existing["simulation_id"],)).fetchone()
                        other_root = str(Path(json.loads(sim_row[0])["root"]) / existing["capture_config"]["output_dir"])
                    current_path, other_path = Path(data["capture_root"]), Path(other_root)
                    if existing["id"] != run_id and (current_path.is_relative_to(other_path) or other_path.is_relative_to(current_path)):
                        raise ValueError("Another run is recording this output folder. Use a unique --output-dir for concurrent runs (and write the simulation output there).")
                baseline_row = conn.execute("SELECT data FROM runs WHERE simulation_id=? AND version=? ORDER BY started_at LIMIT 1", (data["simulation_id"], data["version"])).fetchone()
                baseline = json.loads(baseline_row[0]) if baseline_row else None
                data["source_change"] = "baseline" if not baseline else "same" if baseline["snapshot_id"] == data["snapshot_id"] else "text-only" if baseline["structure_id"] == data["structure_id"] else "changed"
                data["baseline_run_id"] = baseline["id"] if baseline else run_id
                conn.execute("INSERT OR IGNORE INTO runs VALUES (?,?,?,?,?,?)", (run_id, data["simulation_id"], data["status"], data["started_at"], data["version"], json_text(data)))
                boundaries = data.get('swss_output_boundaries')
                if boundaries:
                    # The journaled start and its known generated boundaries
                    # commit together, including during recovery after failure.
                    key = boundaries['key']
                    if not key.startswith('swss_output_boundaries:' + data['simulation_id'] + ':'):
                        raise ValueError('Invalid SWSS output-boundary association')
                    previous = conn.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()
                    paths = sorted(set(boundaries['paths']) | set(json.loads(previous[0]) if previous else []))
                    conn.execute('INSERT OR REPLACE INTO metadata(key,value) VALUES (?,?)', (key, json_text(paths)))
            else:
                row = conn.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
                if not row:
                    raise ValueError("Run has not been initialized")
                run = json.loads(row[0])
                if kind == "parameters":
                    if run["status"] == "running":
                        run["parameters"].update(data["values"])
                        run["parameter_sources"].update({key: data.get("source", "python") for key in data["values"]})
                elif kind == "environment":
                    if run["status"] == "running":
                        run["environment"] = data
                elif kind == "metric":
                    if run["status"] == "running":
                        conn.execute("INSERT OR IGNORE INTO metrics VALUES (?,?,?)", (event["id"], run_id, json_text({**data, "recorded_at": event["at"]})))
                elif kind == "finish":
                    if run["status"] == "running":
                        run.update(data)
                        if progress_error:
                            run["progress_error"] = progress_error
                elif kind == "artifact":
                    if not deleted_screenshot(conn, data["id"]):
                        conn.execute("INSERT OR IGNORE INTO artifacts VALUES (?,?,?)", (data["id"], run_id, json_text(data)))
                elif kind == "annotation":
                    # Preserve the prior display name in append-only history,
                    # including backups that do not retain the start journal.
                    annotation = dict(data)
                    if "name" in data:
                        annotation["previous_name"] = run["name"]
                    for key in ("notes", "tags", "name", "cover_id", "version_note"):
                        if key in data:
                            run[key] = data[key]
                    conn.execute("INSERT OR IGNORE INTO annotations VALUES (?,?,?)", (event["id"], run_id, json_text({**annotation, "at": event["at"]})))
                elif kind == "artifact_annotation":
                    if deleted_screenshot(conn, data["id"]):
                        conn.execute("INSERT INTO applied_events VALUES (?)", (event["id"],))
                        return
                    artifact = conn.execute("SELECT data FROM artifacts WHERE id=? AND run_id=?", (data["id"], run_id)).fetchone()
                    if not artifact:
                        raise ValueError("Attachment not found")
                    payload = json.loads(artifact[0])
                    payload["caption"] = data.get("caption", "")
                    conn.execute("UPDATE artifacts SET data=? WHERE id=?", (json_text(payload), data["id"]))
                    conn.execute("INSERT OR IGNORE INTO annotations VALUES (?,?,?)", (event["id"], run_id, json_text({**data, "at": event["at"]})))
                else:
                    raise ValueError(f"Unknown event type: {kind}")
                if kind not in {"artifact", "metric", "artifact_annotation"}:
                    conn.execute("UPDATE runs SET status=?,data=? WHERE id=?", (run["status"], json_text(run), run_id))
            conn.execute("INSERT INTO applied_events VALUES (?)", (event["id"],))

    @locked_store
    def reconcile(self) -> dict:
        recovered, errors = 0, []
        with self.connection() as conn:
            applied = {row[0] for row in conn.execute("SELECT id FROM applied_events")}
        for file in sorted((self.path / "journal").glob("*/*.json")):
            if file.name == "progress.json":
                continue
            if file.stem in applied:
                continue
            try:
                self.apply(json.loads(file.read_text()))
                recovered += 1
            except (ValueError, OSError, sqlite3.Error) as exc:
                errors.append(f"{file.parent.name}/{file.name}: {exc}")
        from .progress import recover_progress
        for file in (self.path / "journal").glob("*/progress.json"):
            try:
                recover_progress(self, file.parent.name)
            except (ValueError, OSError, sqlite3.Error, KeyError, TypeError) as exc:
                errors.append(f"Progress recovery: {exc}")
        for run in self.runs(status="running", limit=10000):
            owner = run.get("owner", {})
            if owner.get("host") == socket.gethostname() and owner.get("pid") and not process_alive(owner["pid"], owner.get("identity")):
                self.emit(run["id"], "finish", {"status": "interrupted", "ended_at": now(), "exit_code": None, "capture_status": "incomplete", "capture_errors": ["Recorder process ended unexpectedly. Final output capture did not complete."]})
        if not errors:
            try:
                errors.extend(cleanup_removed(self))
            except (ValueError, OSError, sqlite3.Error) as exc:
                errors.append(str(exc))
        return {"recovered": recovered, "errors": errors}

    def remove_runs(self, identifiers, *, confirmed=False):
        return remove_runs(self, identifiers, confirmed=confirmed)

    def runs(self, simulation=None, status=None, search="", version=None, limit=500, offset=0) -> list[dict]:
        where, args = [], []
        for column, value in (("simulation_id", simulation), ("status", status), ("version", version)):
            if value:
                where.append(column + "=?")
                args.append(value)
        sql = "SELECT data FROM runs" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY started_at DESC"
        with self.connection() as conn:
            data = [json.loads(row[0]) for row in conn.execute(sql, args)]
        if search:
            needle = search.casefold()
            data = [r for r in data if needle in " ".join([r.get("name", ""), r["id"], r["version"], r.get("notes", ""), " ".join(r.get("tags", [])), json_text(r.get("parameters", {}))]).casefold()]
        return data[offset:offset + limit]

    @locked_store
    def run(self, ident: str, detail=True) -> dict:
        with self.connection() as conn:
            row = conn.execute("SELECT data FROM runs WHERE id=?", (ident,)).fetchone()
            if not row:
                raise ValueError("Run not found")
            result = json.loads(row[0])
            result["baseline_deleted"] = deleted_run(conn, result.get("baseline_run_id", "")) is not None
            from .progress import enabled
            if enabled(conn):
                progress = conn.execute("SELECT data FROM progress WHERE run_id=?", (ident,)).fetchone()
                result["progress"] = json.loads(progress[0]) if progress else None
            if detail:
                result["artifacts"] = [self.artifact_state(json.loads(r[0])) for r in conn.execute("SELECT data FROM artifacts WHERE run_id=? ORDER BY rowid", (ident,))]
                for artifact in result["artifacts"]:
                    artifact["screenshot_deletion_reason"] = deletion_reason(artifact, result)
                result["metrics"] = [json.loads(r[0]) for r in conn.execute("SELECT data FROM metrics WHERE run_id=? ORDER BY event_id LIMIT 5000", (ident,))]
                result["metric_count"] = conn.execute("SELECT count(*) FROM metrics WHERE run_id=?", (ident,)).fetchone()[0]
                result["annotation_history"] = [json.loads(r[0]) for r in conn.execute("SELECT data FROM annotations WHERE run_id=? ORDER BY event_id DESC LIMIT 100", (ident,))]
                result["snapshot"] = read_snapshot(self.path, result["snapshot_id"])
        return result

    def artifact_state(self, artifact: dict) -> dict:
        if artifact["policy"] == "copy":
            artifact["availability"] = "available" if blob_path(self.path, artifact["blob"]).is_file() else "missing"
        elif artifact["policy"] == "reference":
            path = Path(artifact["original_path"])
            if artifact.get("host") != socket.gethostname():
                artifact["availability"] = "another-computer"
            else:
                try:
                    s = path.stat()
                    artifact["availability"] = "available" if s.st_size == artifact["size"] and s.st_mtime_ns == artifact["mtime_ns"] else "changed"
                except OSError:
                    artifact["availability"] = "missing"
        else:
            artifact["availability"] = "not-captured"
        return artifact

    def artifact(self, ident: str) -> dict:
        with self.connection() as conn:
            row = conn.execute("SELECT data FROM artifacts WHERE id=?", (ident,)).fetchone()
        if not row:
            raise ValueError("Attachment not found")
        return self.artifact_state(json.loads(row[0]))

    def artifact_file(self, ident: str) -> Path:
        artifact = self.artifact(ident)
        if artifact["policy"] != "copy":
            raise ValueError("Referenced files are not served. Open the recorded path on its original computer.")
        path = blob_path(self.path, artifact["blob"])
        if not path.is_file():
            raise ValueError("Saved file is missing")
        return path

    def versions(self, simulation: str) -> list[dict]:
        from .entrypoint_warning import EntrypointWarnings
        warnings = EntrypointWarnings(self)
        groups = {}
        for run in self.runs(simulation=simulation, limit=100000):
            group = groups.setdefault(run["version"], {"version": run["version"], "run_count": 0, "snapshots": set(), "structures": set(), "latest": run["started_at"], "changed": 0})
            group["run_count"] += 1
            group["snapshots"].add(run["snapshot_id"])
            group["structures"].add(run["structure_id"])
            group["changed"] += warnings.check(run)["warn"]
        return [{**g, "snapshots": len(g["snapshots"]), "structures": len(g["structures"])} for g in groups.values()]
