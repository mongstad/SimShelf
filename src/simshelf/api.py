from __future__ import annotations

import asyncio
import difflib
import json
import secrets
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
from .source import blob_path
from .store import Store


class SimulationInput(BaseModel):
    root: str
    name: str | None = None
    entrypoint: str | None = None
    version_file: str | None = None


class SimulationUpdate(BaseModel):
    config: dict | None = None
    name: str | None = None
    description: str | None = None


class RunUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=160)
    notes: str | None = Field(None, max_length=50000)
    tags: list[str] | None = None
    cover_id: str | None = None
    version_note: str | None = Field(None, max_length=10000)


def create_app(workspace=None) -> FastAPI:
    store = Store(workspace)
    token = secrets.token_urlsafe(32)

    async def recover():
        while True:
            await asyncio.to_thread(store.reconcile)
            await asyncio.sleep(5)

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(recover())
        yield
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    app = FastAPI(title="SimShelf", version=__version__, lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.store = store
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

    @app.get("/api/workspace")
    def workspace_info():
        return {"path": str(store.path), "version": __version__, "token": token, "simulation_count": len(store.simulations())}

    @app.get("/api/simulations")
    def simulations():
        return store.simulations()

    @app.post("/api/simulations", status_code=201)
    def add_simulation(body: SimulationInput):
        return store.add_simulation(**body.model_dump())

    @app.patch("/api/simulations/{ident}")
    def update_simulation(ident: str, body: SimulationUpdate):
        return store.update_simulation(ident, **body.model_dump(exclude_unset=True))

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
                run["cover_id"] = run.get("cover_id") or (images[0]["id"] if images else None)
        return result

    @app.get("/api/runs/{ident}")
    def run_detail(ident: str):
        return store.run(ident)

    @app.patch("/api/runs/{ident}")
    def annotate(ident: str, body: RunUpdate):
        store.run(ident, False)
        data = body.model_dump(exclude_unset=True)
        if any(value is None for key, value in data.items() if key != "cover_id"):
            raise ValueError("Use empty text or an empty tag list to clear annotations")
        if data.get("tags") is not None and (len(data["tags"]) > 50 or any(not t or len(t) > 80 for t in data["tags"])):
            raise ValueError("Use up to 50 tags, each containing 1–80 characters")
        if data.get("cover_id"):
            artifact = store.artifact(data["cover_id"])
            if artifact["run_id"] != ident or artifact["policy"] != "copy" or artifact.get("media_type") not in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
                raise ValueError("Choose a saved image from this run")
        store.emit(ident, "annotation", data)
        return store.run(ident)

    @app.get("/api/runs/{ident}/logs")
    def logs(ident: str, stream: str = "stdout"):
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
        run = store.run(ident)
        entry = next((f for f in run["snapshot"]["files"] if f["path"] == path), None)
        if not entry:
            raise ValueError("Source file not found in this snapshot")
        if entry["size"] > 1024 * 1024:
            raise ValueError("Source preview is limited to 1 MB per file")
        text = blob_path(store.path, entry["blob"]).read_bytes().decode(errors="replace")
        if compare:
            other = store.run(compare)
            previous = next((f for f in other["snapshot"]["files"] if f["path"] == path), None)
            old = blob_path(store.path, previous["blob"]).read_text(errors="replace") if previous and previous["size"] <= 1024 * 1024 else ""
            return {"text": "".join(difflib.unified_diff(old.splitlines(True), text.splitlines(True), fromfile=f"{compare[:8]}/{path}", tofile=f"{ident[:8]}/{path}")) or "No changes in this file."}
        return {"text": text}

    @app.post("/api/runs/{ident}/attachments", status_code=201)
    async def upload(ident: str, file: UploadFile):
        store.run(ident, False)
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
        artifact = store.artifact(ident)
        store.emit(artifact["run_id"], "artifact_annotation", {"id": ident, "caption": caption})
        return store.artifact(ident)

    @app.get("/api/artifacts/{ident}/file")
    def artifact_file(ident: str, download: bool = False):
        artifact = store.artifact(ident)
        safe_inline = {"image/png", "image/jpeg", "image/webp", "image/gif", "video/mp4", "text/plain", "text/csv", "application/json"}
        media = artifact.get("media_type", "application/octet-stream")
        return FileResponse(store.artifact_file(ident), media_type=media if media in safe_inline else "application/octet-stream", filename=clean_name(artifact["name"]), content_disposition_type="attachment" if download or media not in safe_inline else "inline")

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
