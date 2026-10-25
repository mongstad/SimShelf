import {build} from 'esbuild';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
const destination=process.argv[2];
if(!destination || !resolve(destination).startsWith('/tmp/'))throw Error('Supply a disposable /tmp/ directory');
await mkdir(destination,{recursive:true});
await build({entryPoints:['frontend/rename-run.browser.test.mjs'],bundle:true,format:'esm',outfile:resolve(destination,'test.js')});
await writeFile(resolve(destination,'index.html'),'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Run rename regression</title><link rel="stylesheet" href="test.css"><div id="root"></div><script type="module" src="test.js"></script></html>');
console.log(destination);
