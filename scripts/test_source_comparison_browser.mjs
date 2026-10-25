import { build } from 'esbuild';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
const destination=process.argv[2];
if(!destination||!resolve(destination).startsWith('/tmp/'))throw Error('Supply a disposable /tmp/ directory');
await mkdir(destination,{recursive:true});
await build({entryPoints:['frontend/source-comparison.browser.test.mjs'],bundle:true,format:'esm',outfile:resolve(destination,'test.js'),define:{'process.env.NODE_ENV':'"development"'}});
await writeFile(resolve(destination,'index.html'),'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Source comparison regression</title><link rel="stylesheet" href="test.css"><body style="overflow:auto"><main style="max-width:900px;margin:auto;padding:20px"><button id="run-tests">Run source regression tests</button><pre id="results" role="status"></pre><div id="root"></div></main><script type="module" src="test.js"></script></body></html>');
