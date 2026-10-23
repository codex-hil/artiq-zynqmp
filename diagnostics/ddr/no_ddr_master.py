"""Diagnostic request tie-offs, no transaction-history claim; LGPL-3.0-or-later."""
import re

def disable_pl_masters(module, ps):
    """Tie every exported PS slave AXI request channel inactive; fail closed."""
    ports={}
    for name in ps.inputs:
        match=re.fullmatch(r'(saxigp\d+)_(ar|aw|w)valid',name)
        if name.startswith('saxi') and name.endswith('valid') and not match:
            raise ValueError('Unreviewed slave AXI request '+name)
        if match:ports.setdefault(match[1],set()).add(match[2])
    if not ports or any(channels!={'ar','aw','w'} for channels in ports.values()):
        raise ValueError('Complete exported slave AXI channel inventory required')
    names=sorted(prefix+'_'+channel+'valid' for prefix in ports for channel in ('ar','aw','w'))
    for name in names:module.comb += ps.inputs[name].eq(0)
    for name,signal in ps.inputs.items():
        if re.fullmatch(r'saxi(?:hp\d+_fpd|lpd)_aclk',name):module.comb += signal.eq(module.cd_sys.clk)
    return names
