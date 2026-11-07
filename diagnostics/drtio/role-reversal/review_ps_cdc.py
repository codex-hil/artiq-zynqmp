#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Pin and inspect the installed LiteX reset contract; no hardware access."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path('/srv/codex-hil-data/artiq-zynqmp/reference/litex/litex/soc/interconnect')

def inspect():
    paths = [ROOT / 'axi/axi_lite.py', ROOT / 'stream.py']
    trees = [ast.parse(p.read_text()) for p in paths]
    classes = [{n.name: n for n in tree.body if isinstance(n, ast.ClassDef)} for tree in trees]
    axi = classes[0]['AXILiteClockDomainCrossing']
    stream = classes[1]['ClockDomainCrossing']
    init = next(n for n in stream.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
    defaults = dict(zip([a.arg for a in init.args.args][-len(init.args.defaults):], init.args.defaults))
    assert ast.literal_eval(defaults['with_common_rst']) is False
    crossings = [n for n in ast.walk(axi) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == 'ClockDomainCrossing']
    assert len(crossings) == 5
    assert all(len(n.args) == 3 and not n.keywords for n in crossings)
    return {
        'status': 'SOURCE_CONTRACT_REVIEW_PASS_NOT_CDC_QUALIFIED',
        'sources': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'checks': {'axi_lite_independent_channel_fifos': len(crossings),
                   'stream_common_reset_default': False,
                   'axi_wrapper_requests_common_reset': False},
        'decision': 'Do not adopt stock wrapper as a qualified reset boundary without an external coordinated reset contract.',
        'required_tests': [
            'Unequal PS/master clocks, independent AW/W acceptance and response backpressure',
            'Stop actual destination clock edges; queued request must not fabricate a response',
            'Common asynchronous reset while destination clock is stopped; no stale request after restart',
            'Reset after target accepted a write: outcome remains unknown, no automatic retry',
            'Fresh transaction after coordinated reset and target reinitialization'],
        'simulation_requirement': 'Migen TimeManager schedules domain edges independently of combinational clock assignments; suppress actual scheduled edges or use an HDL simulator. Ready-low is not clock-stop evidence.',
        'other_gates': ['Native AUX binary RX pointer CDC remains unqualified',
                        'Board reset release timing and physical CDC constraints remain unqualified'],
        'hardware_accessed': False,
        'implementation': 'NOT_IMPLEMENTED',
        'dynamic_tests': 'NOT_RUN'}

if __name__ == '__main__':
    print(json.dumps(inspect(), indent=2))
