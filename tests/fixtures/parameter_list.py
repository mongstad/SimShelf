"""Harmless UI fixture: emit received argv, without running a scientific solver.

Run with the installed SimShelf interpreter and a new external directory.
The optional fixture has 77 SWSS declarations; the mixed fixture has six.
"""
from pathlib import Path
import argparse
import sys
from simshelf.store import Store
parser = argparse.ArgumentParser(description="Create disposable parameter-list UI fixtures; never use a scientific workspace.")
parser.add_argument("directory", type=Path, help="New external fixture directory (must not exist)")
base = parser.parse_args().directory.resolve()
if base.is_relative_to(Path(__file__).resolve().parents[2]):
    parser.error("Use a directory outside the checkout")
base.mkdir(parents=True, exist_ok=False)
store=Store(base/'workspace')
for required in [False,True]:
 root=base/('mixed' if required else 'optional');root.mkdir(exist_ok=True)
 (root/'sim.py').write_text('''SIMSHELF_VERSION = "1.0.0"
import os, sys, json
from pathlib import Path
print(json.dumps(sys.argv[1:]), flush=True)
out=Path(os.environ['SIMSHELF_OUTPUT_DIR'])
(out/'run_20261019T000000Z_fixture.log').write_text(json.dumps(sys.argv[1:]))
''')
 names=['queue-zmin','queue-zmax','sponge-width','diag-dt','snapshot-times','precision','no-plots']+[f'diagnostic-{i}-long-parameter-name' for i in range(7,77)]
 text='[swss]\nschema_version=2\nentrypoint="sim.py"\nsimulation_version="1.0.0"\n'
 for i,name in enumerate(names[:6] if required else names):
  flag=i==6 or i>=7 and i%6==0
  typ='boolean' if flag else 'string' if i in [4,5] else 'float'
  text+=f'\n[[swss.parameters]]\nid="p{i}"\nkind="option"\noptions=["--{name}","--alias-{i}"]\nrequired={str(required and i in [0,3]).lower()}\ntype="{typ}"\naction="'+('store_false' if flag else 'store')+'"\nhelp="'+('Disable visualization output.' if flag else f'Diagnostic sampling control {i}; adjust the observation interval without changing other defaults.')+'"\n'
  text+=('default=true\n' if flag else 'default=""\n' if typ=='string' else 'default=0.01\n')
  if i==5:text+='choices=["single","double", ""]\n'
 (root/'swss.toml').write_text(text)
 sim=store.add_simulation(root,name='Required and optional fixture' if required else '77 declaration SWSS fixture',entrypoint='sim.py')
 args=['--queue-zmin','00192','--diag-dt=1e-3','--snapshot-times','','--unknown','--','--no-plots']
 store.update_simulation(sim['id'],execution={'interpreter':sys.executable,'cwd':'.','arguments':args,'output_dir':'outputs','output_policy':'per_run'})
 print(sim['id'],sim['name'])
