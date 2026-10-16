import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
const destination = "src/simshelf/static";
await mkdir(`${destination}/assets`, { recursive: true });
await build({
  entryPoints: ["frontend/main.tsx"],
  bundle: true,
  minify: true,
  sourcemap: false,
  outfile: `${destination}/assets/app.js`,
  target: ["es2022"],
  define: { "process.env.NODE_ENV": '"production"' },
  legalComments: "linked",
});
await writeFile(
  `${destination}/index.html`,
  `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="Your local simulation library and run journal"><title>SimShelf</title><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect width='40' height='40' rx='12' fill='%2325635d'/%3E%3Ctext x='7' y='29' fill='white' font-size='32'%3E∿%3C/text%3E%3C/svg%3E"><link rel="stylesheet" href="/assets/app.css"></head><body><div id="root"></div><script type="module" src="/assets/app.js"></script></body></html>\n`,
);
console.log("Built the bundled browser interface.");
