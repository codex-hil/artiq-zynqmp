"""Read-only same-boot master observations; LGPL-3.0-or-later."""
import hashlib
import json
from pathlib import Path
import capture_zdma_status as zdma
import capture_csu_core_state as csu
import capture_rpu_state as rpu

MODULES={'zdma':zdma,'csu':csu,'rpu':rpu}
SCRIPTS=set.union(*(m.SCRIPTS for m in MODULES.values()))|{'scripts/collect_boot_masters.py'}


def preflight(path):
    items=json.loads(path.read_text())
    if set(items)!=set(MODULES):raise ValueError('Exact master input inventory required')
    for name,module in MODULES.items():
        item=items[name];p=Path(item['path'])
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Changed master inputs '+name)
        module.preflight(p)
    return items


def collect(path,xs,server):
    preflight(path)
    result={}
    for name,module in MODULES.items():
        script={'zdma':'probe_zdma_status.tcl','csu':'probe_csu_core_state.tcl','rpu':'probe_rpu_state.tcl'}[name]
        result[name]=module.parse(xs('master-'+name,script,server,'210383B7F02DA'))
    return dict(status='SAME_BOOT_MASTER_OBSERVATIONS_ONLY',observations=result,
                necessary_dma_fields_pass=result['zdma']['all_quiet_fields'] and result['csu']['csu']['all_quiet_fields'],
                destructive_test_allowed=False,ownership='NOT_PROVEN',
                limits='Sequential snapshots in one boot, not atomic or exclusive/drain proof; core metadata and RPU bits remain observations.')
