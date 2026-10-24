// Full-App quit fixture; bundle with esbuild and serve outside the checkout.
// Query: mode=idle|active|race|failure|status-failure|unavailable|closing.
const mode = new URLSearchParams(location.search).get("mode") || "idle";
const state = {
  generation: 0,
  active_runs: mode === "active" ? 2 : 0,
  closing: mode === "closing",
  can_quit: mode !== "unavailable",
};
window.fetch = async (url, options = {}) => {
  const path = new URL(url, location.origin).pathname;
  const method = options.method || "GET";
  const body = options.body ? JSON.parse(options.body) : null;
  if (method === "POST") console.info("QUIT REQUEST " + JSON.stringify(body));
  let value,
    status = 200;
  if (path === "/api/workspace")
    value = {
      path: "/disposable/quit-fixture",
      version: "fixture",
      token: "fixture",
    };
  else if (path === "/api/simulations" || path === "/api/runs") value = [];
  else if (path === "/api/workspace/git") value = { connection: null };
  else if (path === "/api/server") {
    if (mode === "status-failure") {
      status = 503;
      value = { detail: "Status unavailable. Try again." };
    } else value = { ...state };
  } else if (path === "/api/server/quit") {
    if (mode === "race" && state.generation === 0) {
      state.generation = 1;
      state.active_runs = 1;
    }
    if (mode === "failure") throw Error("Connection lost");
    if (
      body.generation !== state.generation ||
      (state.active_runs && !body.stop_runs)
    ) {
      status = 400;
      value = {
        detail: "Runs changed since confirmation. Review Quit SimShelf again.",
      };
    } else {
      state.closing = true;
      value = { closing: true };
    }
  } else throw Error("Unmocked " + path);
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
};
await import("./main");
