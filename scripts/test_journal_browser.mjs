// Build the full-application browser harness outside the checkout, then serve it
// with e.g. python -m http.server 8762 --bind 127.0.0.1 --directory <destination>.
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
const destination = process.argv[2];
if (!destination || !resolve(destination).startsWith("/tmp/"))
  throw Error("Supply a disposable /tmp/ output directory");
await mkdir(destination, { recursive: true });
await build({
  entryPoints: ["frontend/journal.browser.test.mjs"],
  bundle: true,
  format: "esm",
  outfile: resolve(destination, "test.js"),
  define: { "process.env.NODE_ENV": '"development"' },
});
await writeFile(
  resolve(destination, "index.html"),
  '<!doctype html><html><head><meta charset="utf-8"><title>SimShelf journal regression tests</title><link rel="stylesheet" href="test.css"></head><body><button id="run-tests">Run journal regression tests</button><pre id="results" role="status"></pre><div id="root"></div><script type="module" src="test.js"></script></body></html>',
);
console.log(`Browser harness built in ${destination}`);
