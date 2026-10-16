import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
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
// Include the complete licenses, not only the abbreviated bundle comments.
// Resolve scheduler through react-dom so pnpm's dependency isolation is respected.
const require = createRequire(import.meta.url);
const reactDomPackage = require.resolve("react-dom/package.json");
const packagePaths = [
  require.resolve("react/package.json"),
  reactDomPackage,
  createRequire(reactDomPackage).resolve("scheduler/package.json"),
];
const licenses = await Promise.all(
  packagePaths.map(async (packagePath) => {
    const info = JSON.parse(await readFile(packagePath, "utf8"));
    const license = await readFile(join(dirname(packagePath), "LICENSE"), "utf8");
    return `${info.name} ${info.version}\n${license.trim()}\n`;
  }),
);
await writeFile(
  `${destination}/assets/THIRD_PARTY_LICENSES.txt`,
  `Bundled third-party licenses\nGenerated from the locked frontend dependencies by frontend/build.mjs.\n\n${licenses.join("\n---\n\n")}`,
);
console.log("Built the bundled browser interface and third-party licenses.");
