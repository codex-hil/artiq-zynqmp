# SPDX-License-Identifier: LGPL-3.0-or-later
"""Candidate strict HPM1 exported-pin wiring, not validated PS IP export.

Port naming follows existing HPM0 helper convention. Fail closed if actual export
is absent/different. Parent supplies independent management clock and must verify
PS address routing; no assumed HPM1 aperture is encoded here.
"""

def _connect_hpm(module,ps,axi,clock,index):
    fields={'aw':'id addr len size burst lock cache prot qos valid ready',
            'ar':'id addr len size burst lock cache prot qos valid ready',
            'w':'data strb last valid ready','b':'id resp valid ready',
            'r':'id data resp last valid ready'}
    clock_name=f'maxihpm{index}_fpd_aclk'
    if clock_name not in ps.inputs or len(ps.inputs[clock_name])!=1:
        raise ValueError('Missing/invalid HPM1 independent clock pin')
    assignments=[ps.inputs[clock_name].eq(clock)]
    for channel,names in fields.items():
        for field in names.split():
            name=f'maxigp{index}_'+channel+field
            signal=getattr(getattr(axi,channel),field)
            expected_input=(field=='ready' if channel in ('aw','w','ar') else field!='ready')
            collection=ps.inputs if expected_input else ps.outputs
            if name not in collection or len(collection[name])!=len(signal):
                raise ValueError('Missing/direction/width mismatch for PS '+name)
            pin=collection[name]
            assignments.append(pin.eq(signal) if expected_input else signal.eq(pin))
    # Validate everything before mutating parent wiring.
    module.comb+=assignments

def connect_management_hpm1(module,ps,axi,clock):
    _connect_hpm(module,ps,axi,clock,1)

def connect_target_hpm0(module,ps,axi,clock):
    _connect_hpm(module,ps,axi,clock,0)
