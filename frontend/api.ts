let token = "";
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-SimShelf-Token": token,
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : JSON.stringify(body.detail),
    );
  }
  return response.json();
}
export async function connect() {
  const info = await api<{ path: string; version: string; token: string }>(
    "/workspace",
  );
  token = info.token;
  return info;
}
export async function uploadFile(runId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`/api/runs/${runId}/attachments`, {
    method: "POST",
    headers: { "X-SimShelf-Token": token },
    body: form,
  });
  if (!response.ok)
    throw new Error((await response.json()).detail || "Attachment failed");
  return response.json();
}
export async function downloadBackup() {
  const response = await fetch("/api/backup", {
    method: "POST",
    headers: { "X-SimShelf-Token": token },
  });
  if (!response.ok)
    throw new Error((await response.json()).detail || "Backup failed");
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = `simshelf-backup-${new Date().toISOString().slice(0, 10)}.zip`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
