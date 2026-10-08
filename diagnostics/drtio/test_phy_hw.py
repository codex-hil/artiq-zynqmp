#!/usr/bin/env python3
"""GTH internal PMA PRBS7 loopback/clock activity; not a remote DRTIO test.

Requires diagnostic PL already loaded, PS clocks/AXI initialized, all CPUs
halted. Does not program PL, change Si5342 or enable the external SFP TX.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('server', 'cable', 'csr-map', 'output'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--cycles', type=int, default=3)
    args = p.parse_args()
    if args.cycles < 1: p.error('--cycles must be positive')
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    mapping = json.loads(Path(args.csr_map).read_text())
    if mapping.get('magic') != 0x44525430: p.error('Expected diagnostic CSR map')
    # Shell commands are structured argv; Tcl receives server/cable as argv.
    regs = mapping['registers']
    tcl = ['lassign $argv server cable', 'connect -url $server', 'set matches {}',
        'foreach p [targets -target-properties -filter {name == "PSU"}] {',
        ' if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}',
        '}', 'if {[llength $matches] != 1} {error "Exact Genesys cable not found"}',
        'targets -set [lindex $matches 0]', 'configparams force-mem-accesses 1']
    for name, reg in regs.items():
        if reg['words'] != 1: raise ValueError('Diagnostic expects single-word CSRs')
        tcl.append(f'set addr({name}) {reg["address"]}')
    tcl.append('''
proc wr {name value} {global addr; mwr $addr($name) $value}
proc rd {name} {global addr; return [expr {wide([mrd -value $addr($name)]) & 0xffffffff}]}
if {[rd monitor_magic] != 0x44525430} {error "Wrong PL map; refusing writes"}
proc snapshot {} {
 wr monitor_snapshot 1
 return [list [rd monitor_status] [rd monitor_boot_ticks] [rd monitor_rx_ticks] [rd monitor_tx_ticks] [rd monitor_prbs_errors]]
}
wr monitor_tx_enable 0
''')
    tcl.append(f'for {{set cycle 0}} {{$cycle < {args.cycles}}} {{incr cycle}} {{')
    tcl.append('''
 wr monitor_reset 1
 wr monitor_loopback 2
 wr monitor_prbs 1
 wr monitor_tx_prbs 1
 after 50
 wr monitor_reset 0
 set deadline [expr {[clock milliseconds]+10000}]
 while {1} {
  set status [lindex [snapshot] 0]
  if {($status & 0x7f) == 0x7f} {break}
  if {[clock milliseconds] > $deadline} {error "GTH reset/clock timeout status=$status"}
  after 50
 }
 # Ignore PRBS checker acquisition errors, then measure a settled interval.
 after 1000
 set before [snapshot]
 after 1000
 set after_value [snapshot]
 set db [expr {([lindex $after_value 1]-[lindex $before 1]) & 0xffffffff}]
 set dr [expr {([lindex $after_value 2]-[lindex $before 2]) & 0xffffffff}]
 set dt [expr {([lindex $after_value 3]-[lindex $before 3]) & 0xffffffff}]
 set de [expr {([lindex $after_value 4]-[lindex $before 4]) & 0xffffffff}]
 if {$db < 1000000 || $db > 2000000000} {error "Unreasonable bootstrap interval $db"}
 if {abs(double($dr)/$db-1.0) > 0.01 || abs(double($dt)/$db-1.0) > 0.01} {error "Clock ratio failure boot=$db rx=$dr tx=$dt"}
 if {$de != 0} {error "PRBS7 errors: $de"}
 # Negative control: transmit PRBS15 while the RX checker expects PRBS7.
 # A permanently-zero or disconnected error counter must fail this test.
 wr monitor_tx_prbs 2
 after 100
 set bad [snapshot]
 set injected [expr {([lindex $bad 4]-[lindex $after_value 4]) & 0xffffffff}]
 if {$injected == 0} {error "PRBS mismatch did not register errors"}
 wr monitor_reset 1
 wr monitor_tx_prbs 1
 after 50
 wr monitor_reset 0
 set deadline [expr {[clock milliseconds]+10000}]
 while {1} {
  set status [lindex [snapshot] 0]
  if {($status & 0x7f) == 0x7f} {break}
  if {[clock milliseconds] > $deadline} {error "GTH recovery reset timeout status=$status"}
  after 50
 }
 after 1000
 set recovered [snapshot]
 after 500
 set verified [snapshot]
 set recovery_errors [expr {([lindex $verified 4]-[lindex $recovered 4]) & 0xffffffff}]
 if {$recovery_errors != 0} {error "PRBS7 did not recover: $recovery_errors"}
 puts "PHY_NEGATIVE_CONTROL cycle=$cycle mismatch_errors=$injected recovery_errors=$recovery_errors"
 puts "PHY_RESULT cycle=$cycle status=[lindex $after_value 0] boot_delta=$db rx_delta=$dr tx_delta=$dt errors=$de"
}
wr monitor_tx_enable 0
puts "TEST GTHE4_INTERNAL_PMA_PRBS7 PASS"
puts "TEST REMOTE_DRTIO NOT_RUN"
disconnect
''')
    script = out/'probe.tcl'
    script.write_text('\n'.join(tcl))
    cmd = ['vivado-container','shell','-c',
           'exec /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb "$@"',
           'xsdb',str(script),args.server,args.cable]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60+args.cycles*15)
    log = proc.stdout+proc.stderr
    (out/'probe.log').write_text(log)
    result = {'kind':'hardware','time':time.time(),'cable':args.cable,
        'scope':'internal PMA PRBS7 and relative clock activity only',
        'remote_drtio_status':'NOT_RUN','si5342_recovered_lock_status':'NOT_RUN',
        'status':'PASS' if proc.returncode == 0 and 'TEST GTHE4_INTERNAL_PMA_PRBS7 PASS' in log else 'FAIL',
        'log':str(out/'probe.log')}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
