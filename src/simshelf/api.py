from __future__ import annotations

import asyncio
import difflib
import json
import os
import ipaddress
import secrets
import sqlite3
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import __version__
from .backup import create_backup
from .capture import preview, save_file
from .common import clean_name
from .source import blob_path, read_snapshot
from .removal import deleted_run
from .screenshots import delete_screenshot
from .workspace_lock import workspace_lock
from .store import Store
from .portal import PortalJobs, execution_settings
from .output_paths import output_review
from .parameters import discover_parameters
from .interpreters import discovery, probe_interpreter, check_dependencies


class OpenFileResponse(FileResponse):
    """Keep the opened inode alive across removal, preserving range responses."""
    def __init__(self, stream, **kwargs):
        self.stream = stream
        super().__init__(f"/proc/self/fd/{stream.fileno()}", stat_result=os.fstat(stream.fileno()), **kwargs)

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            self.stream.close()


class ArchiveRequest(BaseModel):
    path: str = Field('', max_length=4096)
    initialize: bool = False
    confirmed: bool = False
    future: list[str] = Field(default_factory=list, max_length=100)
    artifact_ids: list[str] = Field(default_factory=list, max_length=1000)
    review: dict = Field(default_factory=dict)
    operation: str = Field('', max_length=32)
    expected_connection: dict | None = None
    remap: bool = False


class SimulationInput(BaseModel):
    root: str
    name: str | None = None
    entrypoint: str | None = None
    version_file: str | None = None


class RelocationInput(BaseModel):
    model_config = {"extra": "forbid"}
    path: str = Field('', max_length=4096)
    review: dict = Field(default_factory=dict)
    confirmed: bool = False


class SimulationRemovalInput(BaseModel):
    model_config = {"extra": "forbid", "strict": True}
    typed_name: str = Field(max_length=160)
    revision: str = Field(min_length=64, max_length=64)
    confirmed: bool = False


class SimulationUpdate(BaseModel):
    entrypoint: str | None = None
    config: dict | None = None
    name: str | None = None
    description: str | None = None


class InterpreterInput(BaseModel):
    model_config = {"extra": "forbid"}
    interpreter: str
    confirmed: bool = False


class OutputInput(BaseModel):
    model_config = {"extra": "forbid"}
    cwd: str = "."
    arguments: list[str] = Field(default_factory=list)
    output_dir: str
    output_mappings: list[dict] = Field(default_factory=list)
    output_policy: str = "fixed"


class ExecutionInput(OutputInput):
    parameter_review: dict | None = None
    interpreter: str
    progress_mode: str = "off"


class LaunchInput(ExecutionInput):
    acknowledge_outputs: bool = False
    name: str | None = Field(None, min_length=1, max_length=160)


class QuitInput(BaseModel):
    model_config = {"extra": "forbid"}
    confirmed: bool = False
    generation: int
    stop_runs: bool = False


class RemovalInput(BaseModel):
    model_config = {"extra": "forbid"}
    run_ids: list[str] = Field(min_length=1, max_length=1000)
    confirmed: bool = False


class ScreenshotDeletionInput(BaseModel):
    model_config = {"extra": "forbid"}
    confirmed: bool = False


class ProgressEnableInput(BaseModel):
    model_config = {"extra": "forbid"}
    confirmed: bool = False


class GitPreviewInput(BaseModel):
    model_config = {"extra": "forbid"}
    path: str = Field(min_length=1, max_length=4096)
    simulation_ids: list[str] = Field(max_length=1000)


class GitSelectionInput(BaseModel):
    model_config = {"extra": "forbid"}
    revision: str = Field(max_length=64)
    rules: list[dict] = Field(default_factory=list, max_length=100)
    paths: list[str] = Field(default_factory=list, max_length=100)


class GitReviewInput(BaseModel):
    model_config = {"extra": "forbid"}
    review: dict
    confirmed: bool = False


class GitConnectInput(BaseModel):
    model_config = {"extra": "forbid"}
    preview: dict
    confirmed: bool = False


class ArchiveToggleRequest(BaseModel):
    model_config = {"extra": "forbid", "strict": True}
    enabled: bool


class PreservationRequest(BaseModel):
    model_config = {"extra": "forbid", "strict": True}
    config: dict = Field(default_factory=dict)
    options: dict = Field(default_factory=dict)
    review: dict = Field(default_factory=dict)
    confirmed: bool = False
    artifact_ids: list[str] = Field(default_factory=list, max_length=1000)
    include_notes: bool = False
    operation: str = Field(default="", max_length=32)


class RunUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=160)
    notes: str | None = Field(None, max_length=50000)
    tags: list[str] | None = None
    cover_id: str | None = None
    version_note: str | None = Field(None, max_length=10000)


def create_app(workspace=None, *, request_shutdown=None) -> FastAPI:
    store = Store(workspace)
    token = secrets.token_urlsafe(32)
    jobs = PortalJobs(store)

    async def recover():
        while True:
            await asyncio.to_thread(store.reconcile)
            await asyncio.sleep(5)

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(recover())
        try:
            yield
        finally:
            await asyncio.to_thread(jobs.close)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    app = FastAPI(title="SimShelf", version=__version__, lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.store = store
    app.state.jobs = jobs
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]", "testserver"])

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin:
            parsed = urlsplit(origin)
            if parsed.netloc != request.headers.get("host") or parsed.scheme not in {"http", "https"}:
                return JSONResponse({"detail": "This local app only accepts requests from its own browser page."}, status_code=403)
        if request.url.path.startswith("/api/") and request.method not in {"GET", "HEAD", "OPTIONS"}:
            if not secrets.compare_digest(request.headers.get("x-simshelf-token", ""), token):
                return JSONResponse({"detail": "Refresh SimShelf before saving."}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ValueError)
    async def value_error(_request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @app.post("/api/workspace/progress/enable")
    def enable_progress_endpoint(body: ProgressEnableInput):
        from .progress import enable_progress
        return enable_progress(store, confirmed=body.confirmed)

    from . import git_archive as archive, preservation

    @app.get("/api/workspace/archive")
    def archive_connection():
        return {"connection": archive.get(store, 'connection'), "remembered_connection": archive.get(store, 'last_connection'),
                "status": archive.connection_status(store), "enabled": archive.global_enabled(store)}

    @app.post("/api/workspace/archive/automatic")
    def archive_automatic(body: ArchiveToggleRequest):
        return archive.set_global_enabled(store, body.enabled)

    @app.post("/api/simulations/{ident}/preservation/participation")
    def preservation_participation(ident: str, body: ArchiveToggleRequest):
        return preservation.set_participation(store, ident, body.enabled)

    @app.post("/api/workspace/archive/connect")
    def archive_connect(body: ArchiveRequest):
        try:
            return archive.connect(store, body.path, body.initialize, body.confirmed, body.expected_connection, body.remap)
        except OSError as exc:
            raise ValueError('Archive folder unavailable. Inspect any partially initialized directory before retrying.') from exc

    @app.post("/api/workspace/archive/disconnect")
    def archive_disconnect():
        archive.disconnect(store)
        return {"disconnected": True}

    @app.get("/api/simulations/{ident}/archive")
    def archive_settings(ident: str):
        store.simulation(ident)
        connection = archive.connection_status(store)
        runs = []
        for run in store.runs(simulation=ident, limit=200):
            events = archive.entries(store, run['id'])
            runs.append({'run': run['id'], 'name': run['name'], 'events': events,
                         'preservation': preservation.summary(store, run['id'], events, connection)})
        return {"settings": archive.get(store, 'settings:' + ident),
                "automatic_status": preservation.status(store, ident), "runs": runs}

    @app.post("/api/simulations/{ident}/archive/preview")
    def archive_settings_preview(ident: str, body: ArchiveRequest):
        return archive.settings_preview(store, ident, body.future)

    @app.post("/api/simulations/{ident}/archive/enable")
    def archive_enable(ident: str, body: ArchiveRequest):
        return archive.enable(store, ident, body.review, body.confirmed)

    @app.post("/api/simulations/{ident}/archive/disable")
    def archive_disable(ident: str):
        preservation.set_participation(store, ident, False)
        return {"disabled": True}

    @app.get("/api/runs/{ident}/archive")
    def run_archive(ident: str):
        return archive.view(store, ident)

    @app.post("/api/runs/{ident}/archive/preview")
    def additions_preview(ident: str, body: ArchiveRequest):
        return archive.additions_preview(store, ident, body.artifact_ids)

    @app.post("/api/runs/{ident}/archive/add")
    def archive_add(ident: str, body: ArchiveRequest):
        return archive.additions(store, ident, body.review, body.operation, body.confirmed)

    @app.post("/api/runs/{ident}/archive/retry")
    def archive_retry(ident: str, body: ArchiveRequest):
        if body.confirmed is not True:
            raise ValueError('Confirm retry of the previously approved archive operation.')
        return archive.publish(store, ident)

    @app.get("/api/runs/{ident}/archive/{event_id}/{index}/file")
    def archive_download(ident: str, event_id: str, index: int):
        from urllib.parse import quote
        name, data = archive.download(store, ident, event_id, index)
        return Response(data, media_type='application/octet-stream', headers={
            'Content-Disposition': "attachment; filename*=UTF-8''" + quote(clean_name(name), safe='')})

    @app.get("/api/simulations/{ident}/preservation")
    def preservation_settings(ident: str):
        sim = store.simulation(ident)
        return {"policy": preservation.get(store, 'settings:' + ident),
                "legacy": archive.get(store, 'settings:' + ident) or archive.get(store, 'paused_settings:' + ident), "config": sim['config'],
                "status": preservation.status(store, ident), "connection": archive.connection_status(store)}

    @app.post("/api/simulations/{ident}/preservation/preview")
    def preservation_preview(ident: str, body: PreservationRequest):
        return preservation.preview(store, ident, body.config, body.options)

    @app.post("/api/simulations/{ident}/preservation/save")
    def preservation_save(ident: str, body: PreservationRequest):
        return preservation.save(store, ident, body.review, body.confirmed)

    @app.post("/api/runs/{ident}/preservation/preview")
    def preservation_additions_preview(ident: str, body: PreservationRequest):
        return preservation.additions_preview(store, ident, body.artifact_ids, body.include_notes)

    @app.post("/api/runs/{ident}/preservation/add")
    def preservation_additions(ident: str, body: PreservationRequest):
        return preservation.additions(store, ident, body.review, body.operation, body.confirmed)

    @app.get("/api/runs/{ident}/archive/{event_id}/record")
    def preservation_record(ident: str, event_id: str):
        data = archive.download_record(store, ident, event_id)
        return Response(data, media_type='application/octet-stream', headers={
            'Content-Disposition': 'attachment; filename="preservation-record.json"'})

    @app.get("/api/runs/{ident}/source-file")
    def retained_source_file(ident: str, path: str):
        from urllib.parse import quote
        data = preservation.retained_source(store, ident, path)
        return Response(data, media_type='application/octet-stream', headers={
            'Content-Disposition': "attachment; filename*=UTF-8''" + quote(clean_name(path), safe='')})

    @app.get("/api/workspace")
    def workspace_info():
        with store.connection() as conn:
            schema_version = int(conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0])
        return {"path": str(store.path), "version": __version__, "token": token, "simulation_count": len(store.simulations()), "schema_version": schema_version}

    def require_loopback(request: Request):
        try:
            local = request.client and ipaddress.ip_address(request.client.host).is_loopback
        except ValueError:
            local = False
        if not local:
            raise HTTPException(403, "Quit is available only from this computer.")

    @app.get("/api/server")
    def server_status(request: Request):
        require_loopback(request)
        return {**jobs.shutdown_status(), "can_quit": request_shutdown is not None}

    @app.post("/api/server/quit")
    def quit_server(body: QuitInput, request: Request):
        require_loopback(request)
        if request_shutdown is None:
            raise HTTPException(409, "This launch mode cannot quit from the portal. Stop its server in the original terminal or service manager.")
        if not body.confirmed:
            raise ValueError("Confirm Quit SimShelf explicitly.")
        first = jobs.request_shutdown(body.generation, body.stop_runs)
        # Send acknowledgement before asking the actual hosting server to exit.
        return JSONResponse({"closing": True}, background=BackgroundTask(request_shutdown) if first else None)

    @app.get("/api/workspace/git")
    def git_connection():
        from .git_provenance import connection
        return {"connection": connection(store)}

    @app.post("/api/workspace/git/preview")
    def git_preview(body: GitPreviewInput):
        from .git_provenance import preview
        return preview(store, body.path, body.simulation_ids)

    @app.post("/api/workspace/git/connect")
    def git_connect(body: GitConnectInput):
        from .git_provenance import connect_repository
        if not body.confirmed:
            raise ValueError("Review and confirm this local repository connection.")
        try:
            return connect_repository(store, body.preview)
        except (KeyError, TypeError):
            raise ValueError("Invalid connection preview; review the repository again.")

    @app.post("/api/workspace/git/disconnect")
    def git_disconnect():
        from .git_provenance import disconnect_repository
        return disconnect_repository(store)

    @app.get("/api/simulations/{ident}/git/files")
    def git_files(ident: str):
        from .git_selection import inventory
        return inventory(store, ident)

    @app.post("/api/simulations/{ident}/git/files/preview")
    def git_files_preview(ident: str, body: GitSelectionInput):
        from .git_selection import selection_preview
        return selection_preview(store, ident, body.revision, body.rules)

    @app.post("/api/simulations/{ident}/git/files/save")
    def git_files_save(ident: str, body: GitReviewInput):
        from .git_selection import save_selection
        if not body.confirmed:
            raise ValueError("Review and confirm inclusion preferences explicitly.")
        return save_selection(store, ident, body.review)

    @app.post("/api/simulations/{ident}/git/ignore/preview")
    def git_ignore_preview(ident: str, body: GitSelectionInput):
        from .git_selection import ignore_preview
        return ignore_preview(store, ident, body.revision, body.paths)

    @app.post("/api/simulations/{ident}/git/ignore/apply")
    def git_ignore_apply(ident: str, body: GitReviewInput):
        from .git_selection import apply_ignore
        if not body.confirmed:
            raise ValueError("Review and confirm the .gitignore additions explicitly.")
        return apply_ignore(store, ident, body.review)

    @app.get("/api/simulations/{ident}/git/discovery")
    def simulation_git_discovery(ident: str):
        from .git_provenance import discover
        return discover(store, ident)

    @app.get("/api/simulations/{ident}/git")
    def simulation_git(ident: str):
        from .git_provenance import observe
        return observe(store, store.simulation(ident), history=True)

    @app.get("/api/simulations")
    def simulations():
        # Union supervisor observations around the database read: cover admission
        # and finalization without holding the lifecycle lock over DB/source I/O.
        active = jobs.active_simulations()
        result = store.simulations()
        active |= jobs.active_simulations()
        for simulation in result:
            simulation["administration_active"] |= simulation["id"] in active
        return result

    @app.post("/api/simulations", status_code=201)
    def add_simulation(body: SimulationInput):
        return store.add_simulation(**body.model_dump())

    @app.patch("/api/simulations/{ident}")
    def update_simulation(ident: str, body: SimulationUpdate):
        return store.update_simulation(ident, **body.model_dump(exclude_unset=True))

    @app.get("/api/simulations/{ident}/removal-preview")
    def preview_simulation_removal(ident: str):
        from .simulation_removal import preview
        return preview(store, ident)

    @app.post("/api/simulations/{ident}/remove")
    def remove_simulation(ident: str, body: SimulationRemovalInput):
        from .simulation_removal import remove
        return remove(store, ident, **body.model_dump())

    @app.post("/api/simulations/{ident}/relocation/preview")
    def preview_relocation(ident: str, body: RelocationInput):
        from .relocation import preview
        return preview(store, ident, body.path)

    @app.post("/api/simulations/{ident}/relocation")
    def relocate_simulation(ident: str, body: RelocationInput):
        from .relocation import relocate
        return relocate(store, ident, body.review, body.confirmed)

    @app.get("/api/simulations/{ident}/capture-preview")
    def capture_preview(ident: str):
        return preview(store.simulation(ident))

    @app.post("/api/simulations/{ident}/capture-preview")
    def proposed_preview(ident: str, body: SimulationUpdate):
        from .config import validate_config
        simulation = store.simulation(ident)
        simulation["config"] = validate_config(body.config or simulation["config"])
        return preview(simulation)

    @app.get("/api/simulations/{ident}/versions")
    def versions(ident: str):
        return store.versions(ident)

    @app.get("/api/simulations/{ident}/parameters")
    def parameter_discovery(ident: str, source: str = "swss"):
        if source not in ("swss", "static"):
            raise ValueError("Choose swss or explicit static discovery")
        return discover_parameters(store.simulation(ident), source)

    @app.get("/api/simulations/{ident}/interpreters")
    def list_interpreters(ident: str):
        return discovery(store.simulation(ident))

    @app.post("/api/simulations/{ident}/interpreter/check")
    def check_interpreter(ident: str, body: InterpreterInput):
        store.simulation(ident)
        if not body.confirmed:
            raise ValueError("Confirm that you trust this executable before checking it")
        return probe_interpreter(body.interpreter)

    @app.post("/api/simulations/{ident}/dependencies/check")
    def dependency_check(ident: str, body: InterpreterInput):
        simulation = store.simulation(ident)
        if not body.confirmed:
            raise ValueError("Confirm that you trust this executable before checking dependencies")
        return check_dependencies(simulation, body.interpreter)

    @app.post("/api/simulations/{ident}/execution/outputs")
    def inspect_outputs(ident: str, body: OutputInput):
        from .output_paths import validate_simulation_output_policy
        simulation = store.simulation(ident)
        validate_simulation_output_policy(simulation, body.output_policy)
        return output_review(simulation, body.cwd, body.arguments, body.output_dir, body.output_mappings, body.output_policy)

    @app.post("/api/simulations/{ident}/execution/validate")
    def validate_execution(ident: str, body: ExecutionInput):
        return execution_settings(store.simulation(ident), body.model_dump(), probe=True)

    @app.put("/api/simulations/{ident}/execution")
    def save_execution(ident: str, body: ExecutionInput):
        plan = execution_settings(store.simulation(ident), body.model_dump(), probe=True)
        return store.update_simulation(ident, execution=plan["settings"])

    @app.post("/api/simulations/{ident}/launch", status_code=201)
    def launch(ident: str, body: LaunchInput):
        return jobs.start(ident, body.model_dump(exclude={"name", "acknowledge_outputs"}), body.name, body.acknowledge_outputs)

    @app.post("/api/runs/{ident}/stop", status_code=202)
    def stop_run(ident: str):
        return jobs.stop(ident)

    @app.get("/api/runs")
    def runs(simulation: str | None = None, status: str | None = None, q: str = "", version: str | None = None, limit: int = 500, offset: int = 0):
        if not 1 <= limit <= 1000 or offset < 0:
            raise ValueError("Use a limit of 1–1000 and a nonnegative offset")
        result = store.runs(simulation, status, q, version, limit, offset)
        with store.connection() as conn:
            for run in result:
                images = [json.loads(r[0]) for r in conn.execute("SELECT data FROM artifacts WHERE run_id=?", (run["id"],))]
                images = [a for a in images if a["policy"] == "copy" and a.get("media_type", "") in {"image/png", "image/jpeg", "image/webp", "image/gif"}]
                run["image_count"] = len(images)
                run["archive_commits"] = conn.execute("SELECT count(*) FROM metadata WHERE key LIKE ? OR key LIKE ?", tuple(prefix + "event:" + run["id"] + ":%" for prefix in archive.NAMESPACES)).fetchone()[0]
                run["cover_id"] = run.get("cover_id") if any(a["id"] == run.get("cover_id") for a in images) else (images[0]["id"] if images else None)
        return result

    @app.post("/api/runs/remove")
    def remove_runs(body: RemovalInput):
        return store.remove_runs(body.run_ids, confirmed=body.confirmed)

    @app.post("/api/runs/{ident}/screenshots/{artifact_id}/delete")
    def remove_screenshot(ident: str, artifact_id: str, body: ScreenshotDeletionInput):
        try:
            return delete_screenshot(store, ident, artifact_id, confirmed=body.confirmed)
        except (OSError, sqlite3.Error) as exc:
            raise HTTPException(409, "Screenshot deletion could not be saved. Check workspace write permissions and storage, then refresh before retrying.") from exc

    @app.get("/api/runs/{ident}")
    def run_detail(ident: str):
        return {**store.run(ident), **jobs.control(ident)}

    @app.patch("/api/runs/{ident}")
    def annotate(ident: str, body: RunUpdate):
        with workspace_lock(store.path):
            store.run(ident, False)
            data = body.model_dump(exclude_unset=True)
            if "name" in data:
                if data["name"] is None or not data["name"].strip():
                    raise ValueError("Run name must contain 1–160 characters, including a non-space character")
                data["name"] = data["name"].strip()
            if any(value is None for key, value in data.items() if key != "cover_id"):
                raise ValueError("Use empty text or an empty tag list to clear annotations")
            if data.get("tags") is not None and (len(data["tags"]) > 50 or any(not t or len(t) > 80 for t in data["tags"])):
                raise ValueError("Use up to 50 tags, each containing 1–80 characters")
            if data.get("cover_id"):
                artifact = store.artifact(data["cover_id"])
                if artifact["run_id"] != ident or artifact["policy"] != "copy" or artifact.get("media_type") not in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
                    raise ValueError("Choose a saved image from this run")
            try:
                store.emit(ident, "annotation", data)
            except (OSError, sqlite3.Error) as exc:
                if "name" not in data:
                    raise
                raise HTTPException(409, "Run name could not be confirmed saved. Check library write permissions and free space, then refresh to check the name before retrying.") from exc
            saved = store.run(ident)
        # Match GET's detail shape: replacing the browser's confirmed run must
        # not temporarily erase recorder ownership after an annotation save.
        # Query jobs outside the workspace lock, as launch takes these in reverse.
        return {**saved, **jobs.control(ident)}

    @app.get("/api/runs/{ident}/logs")
    def logs(ident: str, stream: str = "stdout"):
        with workspace_lock(store.path):
            store.run(ident, False)
            if stream not in {"stdout", "stderr"}:
                raise ValueError("Choose stdout or stderr")
            path = store.path / "logs" / ident / (stream + ".log")
            if not path.is_file():
                return {"text": "", "truncated": False}
            with path.open("rb") as file:
                length = path.stat().st_size
                file.seek(max(0, length - 200000))
                text = file.read(200000).decode(errors="replace")
            return {"text": text, "truncated": length > 200000}

    @app.get("/api/runs/{ident}/source")
    def source(ident: str, path: str, compare: str | None = None):
        with workspace_lock(store.path):
            run = store.run(ident)
            entry = next((f for f in run["snapshot"]["files"] if f["path"] == path), None)
            if not entry:
                raise ValueError("Source file not found in this snapshot")
            if entry["size"] > 1024 * 1024:
                raise ValueError("Source preview is limited to 1 MB per file")
            text = preservation.retained_source(store, ident, path).decode(errors="replace")
            if compare:
                with store.connection() as conn:
                    removed = deleted_run(conn, compare)
                if removed and compare == run["baseline_run_id"]:
                    other_snapshot = read_snapshot(store.path, removed["snapshot_id"])
                else:
                    other_snapshot = store.run(compare)["snapshot"]
                previous = next((f for f in other_snapshot["files"] if f["path"] == path), None)
                old = ""
                if previous and previous["size"] <= 1024 * 1024:
                    raw = archive.safe_read(blob_path(store.path, previous["blob"]), 1024 * 1024)
                    if len(raw) != previous['size'] or archive.hash_bytes(raw) != previous['blob']:
                        raise ValueError('Comparison source failed integrity verification.')
                    old = raw.decode(errors="replace")
                return {"text": "".join(difflib.unified_diff(old.splitlines(True), text.splitlines(True), fromfile=f"{compare[:8]}/{path}", tofile=f"{ident[:8]}/{path}")) or "No changes in this file."}
            return {"text": text}

    @app.post("/api/runs/{ident}/attachments", status_code=201)
    async def upload(ident: str, file: UploadFile):
        await asyncio.to_thread(store.run, ident, False)
        name = clean_name(file.filename or "attachment")
        staging = store.path / "staging"
        staging.mkdir(exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=staging, delete=False) as target:
                temporary = Path(target.name)
                size = 0
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > 25 * 1024**2:
                        raise ValueError("Browser attachments are limited to 25 MB each")
                    target.write(chunk)
            result = await asyncio.to_thread(save_file, store, ident, temporary, name=name)
            return result
        finally:
            await file.close()
            if temporary:
                temporary.unlink(missing_ok=True)

    @app.patch("/api/artifacts/{ident}")
    async def artifact_caption(ident: str, request: Request):
        body = await request.json()
        caption = body.get("caption", "")
        if not isinstance(caption, str) or len(caption) > 5000:
            raise ValueError("Caption must be at most 5000 characters")
        def save_caption():
            with workspace_lock(store.path):
                artifact = store.artifact(ident)
                store.emit(artifact["run_id"], "artifact_annotation", {"id": ident, "caption": caption})
                return store.artifact(ident)
        return await asyncio.to_thread(save_caption)

    @app.get("/api/artifacts/{ident}/file")
    def artifact_file(ident: str, download: bool = False):
        with workspace_lock(store.path):
            artifact = store.artifact(ident)
            safe_inline = {"image/png", "image/jpeg", "image/webp", "image/gif", "video/mp4", "text/plain", "text/csv", "application/json"}
            media = artifact.get("media_type", "application/octet-stream")
            stream = preservation.retained_artifact(store, ident)
            return OpenFileResponse(stream, media_type=media if media in safe_inline else "application/octet-stream", filename=clean_name(artifact["name"]), content_disposition_type="attachment" if download or media not in safe_inline else "inline")

    @app.post("/api/backup")
    async def backup():
        folder = Path(tempfile.mkdtemp(prefix="simshelf-download-"))
        destination = folder / "simshelf-backup.zip"
        try:
            await asyncio.to_thread(create_backup, store, destination)
        except BaseException:
            import shutil
            shutil.rmtree(folder)
            raise
        import shutil
        return FileResponse(destination, filename=destination.name, background=BackgroundTask(shutil.rmtree, folder))

    static = Path(__file__).parent / "static"
    if static.is_dir():
        app.mount("/", StaticFiles(directory=static, html=True), name="ui")
    return app
