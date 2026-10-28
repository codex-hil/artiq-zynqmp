# SPDX-License-Identifier: LGPL-3.0-or-later
"""Offline supplied MB_SLEEP sample interpretation. No capture or admission path."""
ADDRESS = 0xffd80000
MASK = 0x10000

def _uint(value,bits,nonzero=False):
    if type(value) is not int or not int(nonzero)<=value<1<<bits:
        raise ValueError('invalid unsigned integer')
    return value

def decode(record,expected_nonce):
    """Report one sampled state; caller-supplied bytes are not authenticated."""
    _uint(expected_nonce,64,True)
    fields={'version','nonce','address','return_code','value'}
    if type(record) is not dict or set(record)!=fields:
        raise ValueError('exact observation fields required')
    if type(record['version']) is not int or record['version']!=1:
        raise ValueError('unsupported observation version')
    if _uint(record['nonce'],64,True)!=expected_nonce:
        raise ValueError('wrong session nonce')
    if _uint(record['address'],32)!=ADDRESS:
        raise ValueError('only PMU_GLOBAL GLOBAL_CNTRL observation allowed')
    rc=record['return_code']
    if type(rc) is not int or not -(1<<31)<=rc<1<<31:
        raise ValueError('invalid transport result')
    if rc:
        if record['value'] is not None:raise ValueError('failed read must have no value')
        state='UNKNOWN'
    else:
        value=_uint(record['value'],32)
        state='SLEEP_SAMPLED' if value&MASK else 'ACTIVE_SAMPLED'
    return {'state':state,'nonce':expected_nonce,'sample_authenticated':False,
            'continuous_sleep_proven':False,'pmu_ram_access_allowed':False,
            'recovery_qualified':False,'deployable':False,'hardware_executed':False,
            'limits':'Offline interpretation only; no interval ownership, freshness authentication, safe transport or hardware execution proof'}

def require_pmu_ram_access(*args,**kwargs):
    raise ValueError('sampled sleep never admits PMU RAM access: interval and independent recovery unqualified')
