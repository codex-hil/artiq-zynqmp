# SPDX-License-Identifier: LGPL-3.0-or-later
"""Read-only frozen offline audit replay. No execution/deployment option."""
import hashlib
import json
from pathlib import Path
import sys

if len(sys.argv) != 1:
    raise ValueError('frozen audit has no execute/deployment options')
sys.dont_write_bytecode = True
root = Path(__file__).resolve().parent
inventory = json.loads((root/'inventory.json').read_text())
actual = set()
for path in root.rglob('*'):
    if path.is_symlink():
        raise ValueError('symlink forbidden in frozen snapshot')
    if path.is_file() and path != root/'inventory.json':
        actual.add(str(path.relative_to(root)))
if actual != set(inventory):
    raise ValueError('frozen snapshot file inventory changed')
for name, digest in inventory.items():
    path = root/name
    if Path(name).is_absolute() or not path.resolve().is_relative_to(root):
        raise ValueError('snapshot path escapes root')
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError('changed frozen input: '+name)
manifest = json.loads((root/'manifest.json').read_text())
for item in manifest['artifacts'].values():
    relative = Path(item['path'])
    path = (root/relative).resolve()
    if relative.is_absolute() or not path.is_relative_to(root):
        raise ValueError('artifact path escapes frozen root')
    item['path'] = str(path)
sys.path.insert(0, str(root/'repo/scripts'))
from pit_ro_composition_audit_gate import audit
print(json.dumps(audit(manifest, root/'repo'), sort_keys=True, indent=2))
