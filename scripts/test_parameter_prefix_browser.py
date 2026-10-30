"""Build a disposable schema-3 editor fixture; never execute the simulation."""
import argparse
import subprocess
from pathlib import Path
import json
from simshelf.parameters import discover_parameters
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('destination', type=Path)
parser.add_argument('--node', default='node')
args = parser.parse_args()
destination = args.destination.resolve()
if not destination.is_relative_to('/tmp') or destination.exists():
    parser.error('Use a new disposable directory under /tmp')
destination.mkdir(parents=True)
root=destination/'fixture';root.mkdir()
(root/'sim.py').write_text('# harmless metadata fixture; never executed\n')
text='[swss]\nschema_version=3\nentrypoint="sim.py"\nsimulation_version="1.0"\n'
for i,name in enumerate(['volume','volume-interval']+[f'parameter-{i}' for i in range(20)]):
    flag=i==0
    text+=f'\n[[swss.parameters]]\nid="p{i}"\nkind="option"\noptions=["--{name}"]\nrequired=false\ntype="{ "boolean" if flag else "float"}"\naction="{"store_true" if flag else "store"}"\nhelp="Fixture"\ndefault={"false" if flag else "1.0"}\n'
(root/'swss.toml').write_text(text)
sim={'root':str(root),'entrypoint':'sim.py','version_file':'sim.py'}
d=discover_parameters(sim)
assert len(d['parameters'])==22,d
assert all(p['supported'] for p in d['parameters']),d
(destination/'discovery.json').write_text(json.dumps(d))

subprocess.run([args.node, '--input-type=module', '-e', """
import {build} from 'esbuild';
import {resolve} from 'node:path';
await build({entryPoints:['frontend/parameterPrefix.browser.test.mjs'],bundle:true,
  format:'esm',outfile:resolve(process.argv[1],'test.js'),
  define:{'process.env.NODE_ENV':'"development"'}});
""", str(destination)], cwd=Path(__file__).resolve().parents[1], check=True)
(destination/'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Parameter prefix regression</title><link rel="stylesheet" href="test.css"></head><body><button id="run-tests">Run tests</button><pre id="results"></pre><div id="root"></div><script type="module" src="test.js"></script></body></html>')
print(destination)
