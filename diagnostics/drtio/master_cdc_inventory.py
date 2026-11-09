# SPDX-License-Identifier: LGPL-3.0-or-later
"""Conservative pre-lowering fragment inventory; NOT a physical CDC checker."""
from collections import Counter
from migen.fhdl.visit import NodeVisitor
from migen.fhdl.tools import list_signals
from migen.genlib.cdc import MultiReg
from migen.genlib.resetsync import AsyncResetSynchronizer

class Assignments(NodeVisitor):
    def __init__(self):self.items=[]
    def visit_Assign(self,node):self.items.append((set(list_signals(node.l)),set(list_signals(node.r))))

def collect(fragment):
    owners={};edges=[]
    for domain,statements in fragment.sync.items():
        visitor=Assignments();visitor.visit(statements)
        for left,right in visitor.items:
            for signal in left:owners.setdefault(signal,set()).add(domain)
    visitor=Assignments();visitor.visit(fragment.comb);edges=visitor.items
    # Propagate known sequential origins through combinational aliases only.
    # Unclocked inputs, special outputs and control dependencies remain unknown.
    changed=True
    while changed:
        changed=False
        for left,right in edges:
            origin=set().union(*(owners.get(s,set()) for s in right))
            for signal in left:
                prior=owners.setdefault(signal,set());n=len(prior);prior.update(origin)
                changed|=len(prior)!=n
    rows=[]
    for special in sorted(fragment.specials,key=lambda s:s.duid):
        if isinstance(special,MultiReg):
            origin=set().union(*(owners.get(s,set()) for s in list_signals(special.i)))
            rows.append({'type':'MultiReg','bits':len(special.i),'stages':special.n,
                         'destination':special.odomain,'known_sequential_origins':sorted(origin),
                         'origin_complete':False,
                         'input_signal_hints':sorted({s.backtrace[-1][0] if s.backtrace else 'unnamed' for s in list_signals(special.i)})})
        elif isinstance(special,AsyncResetSynchronizer):
            rows.append({'type':'AsyncResetSynchronizer','destination':special.cd.name,
                         'assertion_qualified':False})
    return {'status':'PRELOWERING_STRUCTURAL_INVENTORY_ONLY','rows':rows,
            'counts':dict(Counter(row['type'] for row in rows)),
            'clock_domains':sorted(cd.name for cd in fragment.clock_domains),
            'clock_source_contract':{'pl_clk0':['management','control','ps'],
              'phy_tx_clock':['sys','rio','rio_phy'],'phy_rx_clock':['rtio_rx','gt_align']},
            'limits':['Not post-synthesis CDC or endpoint/constraint matching',
              'Origin propagation incomplete: special outputs/control dependencies not inferred',
              'MultiReg presence/stage count is not physical signoff',
              'Shared physical source does not establish safe reset/CDC semantics',
              'No false-path, clock-group, skew or max-delay exceptions generated']}
