#!/usr/bin/env python3
"""Offline XSA DDR-master inventory, never runtime admission; LGPL-3.0-or-later."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

PORTS=([f'PSU__USE__M_AXI_GP{i}' for i in range(3)]+
       [f'PSU__USE__S_AXI_GP{i}' for i in range(7)]+
       ['PSU__USE__S_AXI_ACE','PSU__USE__S_AXI_ACP','PSU__USE__ADMA','PSU__USE__GDMA'])


def parameters(hwh):
    root=ET.fromstring(hwh)
    modules=[m for m in root.iter('MODULE') if m.get('MODTYPE')=='zynq_ultra_ps_e']
    if len(modules)!=1:raise ValueError('Expected exactly one ZynqMP PS module')
    result={}
    containers=modules[0].findall('PARAMETERS')
    if len(containers)!=1:raise ValueError('Expected direct PS parameter container')
    for p in containers[0].findall('PARAMETER'):
        name=p.get('NAME');value=p.get('VALUE')
        if not name or name in result:raise ValueError('Missing/duplicate PS parameter name')
        # Optional preset/QoS entries can legitimately omit VALUE. Required
        # ownership-related booleans are checked separately below.
        result[name]=value
    for name in PORTS:
        if result.get(name) not in ('0','1'):raise ValueError('Missing/nonboolean parameter: '+name)
    return result


def inventory(path):
    with zipfile.ZipFile(path) as z:
        names=[n for n in z.namelist() if n.endswith('.hwh')]
        if len(names)!=1:raise ValueError('Expected one HWH member')
        data=z.read(names[0]);params=parameters(data)
    return dict(status='OFFLINE_DDR_MASTER_INVENTORY_NOT_ADMITTED',hardware_executed=False,
        xsa_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),hwh_sha256=hashlib.sha256(data).hexdigest(),
        configured_ports={n:params[n]=='1' for n in PORTS},
        enabled_peripherals={n:v for n,v in params.items() if n.endswith('__PERIPHERAL__ENABLE') and v=='1'},
        required_runtime_ownership=[
            dict(master='A53 CPU1/2/3',status='NOT_PROVEN',required='Positive stopped/reset states after FSBL, cache/coherency ownership; catch stop is not proof.'),
            dict(master='R5 CPU0/1',status='NOT_PROVEN',required='Verified held-reset/idle policy and no PMU release during test.'),
            dict(master='PMU firmware',status='ACTIVE_NOT_AUDITED',required='Audit linked firmware callbacks/DDR accesses; cannot treat running MicroBlaze as absent.'),
            dict(master='PS ADMA/GDMA',status='NOT_PROVEN',required='Per-channel enable/state and ownership proof. XSA USE=0 does not establish physical reset/quiescence.'),
            dict(master='CSU/PCAP DMA',status='NOT_PROVEN',required='Completion/drain state and exclusive owner; no ISR-clear substitutes.'),
            dict(master='PS GEM/SD/USB/SATA/PCIe',status='NOT_PROVEN',required='Inventory enabled blocks; runtime/reset/traffic ownership before destructive writes.'),
            dict(master='PL HP0 RTIO DMA reader',status='NOT_PROVEN',required='Bind active bitstream to source; prevent new requests AND prove outstanding reads drained, not just enable=0.')],
        destructive_test_allowed=False,
        limits='Selected static XSA only, not current live configuration, active bitstream binding, disabled hardware, bus drain or writable DDR ownership.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--xsa',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=inventory(a.xsa)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
