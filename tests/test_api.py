from fastapi.testclient import TestClient

from simshelf.api import create_app
from simshelf.recording import Run


def test_api_registration_annotation_upload_and_protection(project):
    store, sim, root, source = project
    with Run(sim["id"], workspace=store.path, parameters={"dt": 0.001}, capture_console=False) as run:
        pass
    with TestClient(create_app(store.path)) as client:
        info = client.get("/api/workspace").json()
        headers = {"X-SimShelf-Token": info["token"]}
        assert client.get("/api/simulations").json()[0]["id"] == sim["id"]
        assert client.patch(f"/api/runs/{run.id}", json={"notes": "blocked"}).status_code == 403
        assert client.patch(f"/api/runs/{run.id}", headers={**headers, "Origin": "https://unrelated.example"}, json={"notes": "blocked"}).status_code == 403
        response = client.patch(f"/api/runs/{run.id}", headers=headers, json={"notes": "Good result", "tags": ["baseline"]})
        assert response.status_code == 200
        assert response.json()["notes"] == "Good result"
        assert response.json()["parameters"]["dt"] == .001
        upload = client.post(f"/api/runs/{run.id}/attachments", headers=headers, files={"file": ("../../note.txt", b"saved attachment", "text/plain")})
        assert upload.status_code == 201
        artifact = upload.json()
        assert artifact["name"] == "note.txt"
        assert client.get(f"/api/artifacts/{artifact['id']}/file").text == "saved attachment"
        assert client.get(f"/api/runs/{run.id}/source", params={"path": "../../private"}).status_code == 400
        assert client.get("/api/runs?q=Good").json()[0]["id"] == run.id
        assert client.get("/api/runs?version=missing").json() == []
        assert client.get("/api/workspace", headers={"Host": "attacker.example"}).status_code == 400


def test_api_keeps_active_content_as_downloads(project):
    store, sim, root, source = project
    with Run(sim["id"], workspace=store.path, capture_console=False) as run:
        pass
    with TestClient(create_app(store.path)) as client:
        token = client.get("/api/workspace").json()["token"]
        uploaded = client.post(f"/api/runs/{run.id}/attachments", headers={"X-SimShelf-Token": token}, files={"file": ("diagram.svg", b'<svg onload="alert(1)"></svg>', "image/svg+xml")}).json()
        result = client.get(f"/api/artifacts/{uploaded['id']}/file")
        assert result.headers["content-type"] == "application/octet-stream"
        assert "attachment" in result.headers["content-disposition"]
        assert result.headers["x-content-type-options"] == "nosniff"


def test_source_diff_shows_comment_changes_even_when_structure_matches(project):
    store, sim, root, source = project
    with Run(sim["id"], workspace=store.path, capture_console=False) as first:
        pass
    source.write_text(source.read_text() + "# useful explanation\n")
    with Run(sim["id"], workspace=store.path, capture_console=False) as second:
        pass
    with TestClient(create_app(store.path)) as client:
        response = client.get(f"/api/runs/{second.id}/source", params={"path": "field.py", "compare": first.id})
        assert response.status_code == 200
        assert "+# useful explanation" in response.json()["text"]
        assert client.get(f"/api/runs/{second.id}").json()["source_change"] == "text-only"
