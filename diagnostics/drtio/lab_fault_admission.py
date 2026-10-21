"""Offline artifact admission for the future lab parent; LGPL-3.0-or-later.

Not an execution entry point. Normal ExternalSession still refuses lab firmware.
Active mode additionally requires exact prior hardware idle/counter qualification.
"""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCES=Path(__file__).parent/'aux_protocol'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(config,firmware,mapping):
    mode=config.get('lab_fault_mode')
    if mode not in ('idle','active') or config.get('lab_fault_ack')!='native-underflow-no-reuse':
        raise ValueError('Explicit laboratory mode/acknowledgement required')
    if not (firmware.get('native_ddma') and firmware.get('lab_read_delay')):
        raise ValueError('Dedicated native laboratory firmware required')
    if config.get('native_ddma_mode')!=('idle' if mode=='idle' else 'playback'):
        raise ValueError('Lab/native mode mismatch')
    if not all(config.get(k) for k in ('reset_test','dio_test','snapshot_test')) or any(
        config.get(k) for k in ('host_dma_test','stability_test','recovery_test','native_ddma_catch',
        'native_ddma_cursor','native_ddma_rejection','native_ddma_expired_start',
        'native_ddma_lifecycle','native_ddma_fragmentation','native_ddma_long_lifecycle')):
        raise ValueError('Standalone reset/DIO/snapshot laboratory session required')
    sys.path.insert(0,str(SOURCES))
    from lab_delay_build import validate_map,source_overlay
    if validate_map(mapping)!=firmware.get('lab_read_delay_cycles'):
        raise ValueError('Lab cycle count mismatch')
    expected=hashlib.sha256(source_overlay((SOURCES/'firmware.c').read_text()).encode()).hexdigest()
    if firmware.get('c_source_sha256')!=expected:raise ValueError('Stale generated laboratory C overlay')
    for group,names in [('lab_sources',('ddma_lab_delay.h','ddma_lab_runtime.h','ddma_lab_admission.h','lab_delay_build.py')),
                        ('ddma_sources',('ddma_runtime.h','ddma_service.h','ddma_store.h','ddma_backend.h','ddma_a53.h','ddma_codec.h'))]:
        for name in names:
            if firmware.get(group,{}).get(name)!=digest(SOURCES/name):raise ValueError('Stale lab helper '+name)
    if digest(config['firmware'])!=firmware.get('elf_sha256') or digest(config['csr_map'])!=firmware.get('csr_map_sha256'):
        raise ValueError('Lab firmware/map digest mismatch')
    bit=Path(config['bitstream']);build=json.loads((bit.parent/'results.json').read_text())
    cdc=json.loads((bit.parent/'dma-cdc-results.json').read_text())
    if build.get('status')!='PASS' or cdc.get('status')!='PASS' or (cdc.get('groups'),cdc.get('endpoints'))!=(9,202):
        raise ValueError('Qualified 9-group/202-endpoint implementation required')
    for name in ('top.bit','top.v','top.xdc','csr-map.json','top_timing.rpt','top_bus_skew.rpt'):
        if digest(bit.parent/name)!=build.get('sha256',{}).get(name):raise ValueError('Stale implementation '+name)
    if digest(config['csr_map'])!=build['sha256']['csr-map.json']:raise ValueError('Wrong implementation map')
    for name,sha in cdc.get('sha256',{}).items():
        if digest(bit.parent/name)!=sha:raise ValueError('Stale routed CDC '+name)
    if mode=='active':
        if not config.get('lab_idle_qualification'):raise ValueError('Prior lab idle proof path required')
        proof=json.loads(Path(config['lab_idle_qualification']).read_text());ext=proof.get('external_rx',{})
        if (proof.get('status')!='PASS' or proof.get('restoration')!='PASS' or
            any(ext.get(k)!='PASS' for k in ('restoration','dio_loopback','tsc_snapshot','lab_idle_counters')) or
            ext.get('firmware_sha256')!=firmware['elf_sha256'] or ext.get('bit_sha256')!=build['sha256']['top.bit']):
            raise ValueError('Exact prior lab idle/counter/DIO/snapshot/restoration proof required')
        if not config.get('dma_cursor_overlay'):raise ValueError('Validated host DMA cursor overlay required')
        from prepare_dma_cursor_overlay import validate as validate_cursor
        validate_cursor(config['dma_cursor_overlay'])
    return dict(mode=mode,generated_c_sha256=expected,hardware_access=False,
                scope='ARTIFACT_ADMISSION_ONLY_NOT_EXECUTION_OR_RESTORATION')
