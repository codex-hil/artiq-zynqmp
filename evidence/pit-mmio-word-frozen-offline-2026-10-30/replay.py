# SPDX-License-Identifier: LGPL-3.0-or-later
"""Offline frozen replay; independently recorded inventory digest required."""
import argparse,hashlib,json,re,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--inventory-sha256',required=True)
a=p.parse_args()
if not re.fullmatch('[0-9a-f]{64}',a.inventory_sha256):raise ValueError('invalid inventory anchor')
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parent
raw=(root/'inventory.json').read_bytes()
if hashlib.sha256(raw).hexdigest()!=a.inventory_sha256:raise ValueError('inventory differs from independent anchor')
inventory=json.loads(raw)
actual=set()
for path in root.rglob('*'):
    if path.is_symlink():raise ValueError('snapshot symlink forbidden')
    if path.is_file() and path!=root/'inventory.json':actual.add(str(path.relative_to(root)))
if actual!=set(inventory):raise ValueError('snapshot inventory changed')
for name,digest in inventory.items():
    path=root/name
    if Path(name).is_absolute() or not path.resolve().is_relative_to(root):raise ValueError('snapshot path escapes root')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('changed frozen file: '+name)
manifest=json.loads((root/'manifest.json').read_text())
for item in manifest['artifacts'].values():
    rel=Path(item['path']);path=(root/rel).resolve()
    if rel.is_absolute() or not path.is_relative_to(root):raise ValueError('artifact path escapes snapshot')
    item['path']=str(path)
sys.path.insert(0,str(root/'repo/scripts'))
from pit_mmio_word_audit_gate import audit
print(json.dumps(audit(manifest,root/'repo'),sort_keys=True,indent=2))
