"""Package generated AXAU15 inputs without Trenz host scripts or hardware access."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
p = argparse.ArgumentParser()
p.add_argument('generated', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
metadata = json.loads((a.generated / 'target.json').read_text())
if metadata['board'] != 'AXAU15':
    raise SystemExit('Wrong target')
a.output.mkdir(parents=True, exist_ok=False)
for f in [a.generated / 'axau15_awg.v', a.generated / 'target.json',
          *a.generated.glob('*.init'), root / 'gateware/spi-console.v',
          root / 'axau15/constraints.tcl', root / 'axau15/build.tcl']:
    shutil.copyfile(f, a.output / f.name)
manifest = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(a.output.iterdir())}
manifest = {'inputs': manifest,
            'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
            'status': subprocess.check_output(['git', 'status', '--short'], cwd=root, text=True),
            'hardware': False}
(a.output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
(a.output / 'tracked.diff').write_bytes(subprocess.check_output(['git', 'diff', 'HEAD', '--', str(root)], cwd=root))
