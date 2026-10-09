#!/usr/bin/env python3
"""Validate actual RT/AUX framing through internal GTH PMA loopback.

Requires the --protocol diagnostic PL, initialized PS/AXI and halted A53s.
Leaves external SFP TX disabled; does not touch Si5342 or non-Genesys cables.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('server','cable','csr-map','output'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--cycles',type=int,default=3)
    a=p.parse_args()
    if a.cycles<1: p.error('cycles must be positive')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    mapping=json.loads(Path(a.csr_map).read_text())
    if mapping.get('magic')!=0x44525430 or 'protocol_alignment' not in mapping['registers']:
        p.error('Requires the protocol diagnostic CSR map')
    script=['lassign $argv server cable','connect -url $server','set matches {}',
        'foreach p [targets -target-properties -filter {name == "PSU"}] {',
        'if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}',
        '}','if {[llength $matches]!=1} {error "Exact Genesys target missing"}',
        'targets -set [lindex $matches 0]','configparams force-mem-accesses 1']
    for name,r in mapping['registers'].items():
        if r['words']!=1: raise ValueError('Expected single-word registers')
        script.append(f'set addr({name}) {r["address"]}')
    script.append('''
proc wr {n v} {global addr; mwr $addr($n) $v}
proc rd {n} {global addr; return [expr {wide([mrd -value $addr($n)]) & 0xffffffff}]}
proc delta {a b} {return [expr {($b-$a)&0xffffffff}]}
proc counts {} {
 set r {}
 foreach k {rt_words rt_frames rt_errors aux_words aux_frames aux_errors} {lappend r [rd protocol_$k]}
 return $r
}
if {[rd monitor_magic]!=0x44525430} {error "Wrong loaded PL; refusing writes"}
wr monitor_tx_enable 0
''')
    script.append(f'for {{set cycle 0}} {{$cycle<{a.cycles}}} {{incr cycle}} {{')
    script.append('''
 wr monitor_reset 1
 wr monitor_prbs 0
 wr monitor_tx_prbs 0
 wr monitor_loopback 2
 wr protocol_enable 0
 wr protocol_inject 0
 after 50
 wr monitor_reset 0
 set deadline [expr {[clock milliseconds]+10000}]
 while {1} {
  wr monitor_snapshot 1
  set status [rd monitor_status]
  set alignment [rd protocol_alignment]
  if {($status&0x7f)==0x7f && ($alignment&1)} {break}
  if {[clock milliseconds]>$deadline} {error "PHY/alignment timeout status=$status alignment=$alignment"}
  after 50
 }
 wr protocol_enable 1
 after 500
 set before [counts]
 after 500
 set after_value [counts]
 set deltas {}
 foreach x $before y $after_value {lappend deltas [delta $x $y]}
 foreach {words frames errors} $deltas {
  if {$frames<1000 || $words<10*$frames || $words>24*$frames || $errors!=0} {error "RT/AUX payload or framing failure cycle=$cycle deltas=$deltas"}
 }
 # Alter one bit of encoded RT symbols; prove receiver-side checks respond.
 wr protocol_inject 1
 after 100
 set corrupted [counts]
 set injected [delta [lindex $after_value 2] [lindex $corrupted 2]]
 if {$injected<100} {error "Corruption was not detected: $injected"}
 wr protocol_inject 0
 after 100
 set recovered [counts]
 after 250
 set verified [counts]
 foreach i {2 5} {
  if {[delta [lindex $recovered $i] [lindex $verified $i]]!=0} {error "Packet verification failed after corruption recovery"}
 }
 puts "PROTOCOL_RESULT cycle=$cycle alignment=$alignment rt_words=[lindex $deltas 0] rt_frames=[lindex $deltas 1] rt_errors=[lindex $deltas 2] aux_words=[lindex $deltas 3] aux_frames=[lindex $deltas 4] aux_errors=[lindex $deltas 5] injected=$injected"
}
wr protocol_enable 0
wr protocol_inject 0
wr monitor_tx_enable 0
puts "TEST ARTIQ_GTH_RT_AUX_LOOPBACK PASS"
puts "TEST REMOTE_DRTIO NOT_RUN"
disconnect
''')
    tcl=out/'probe.tcl';tcl.write_text('\n'.join(script)+'\n')
    cmd=['vivado-container','shell','-c','exec /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb "$@"','xsdb',str(tcl.resolve()),a.server,a.cable]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=60+a.cycles*15)
    log=r.stdout+r.stderr;(out/'probe.log').write_text(log)
    ok=r.returncode==0 and 'TEST ARTIQ_GTH_RT_AUX_LOOPBACK PASS' in log
    result={'kind':'hardware','time':time.time(),'status':'PASS' if ok else 'FAIL',
        'scope':'upstream ARTIQ 8b10b and RT/AUX link framing over physical internal GTH PMA loopback',
        'cycles':a.cycles,'cable':a.cable,'external_sfp_tx':'disabled',
        'remote_drtio':'NOT_RUN','deterministic_latency':'NOT_RUN',
        'results':[line for line in log.splitlines() if line.startswith('PROTOCOL_RESULT')],
        'csr_map_sha256':hashlib.sha256(Path(a.csr_map).read_bytes()).hexdigest(),
        'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));
    if not ok: print(log[-5000:])
    return 0 if ok else 1

if __name__=='__main__':raise SystemExit(main())
