#!/usr/bin/env python3
"""Physical time-slotted RT packets through one GTH PMA loopback.

Requires packet diagnostic PL and halted A53s. LGPL-3.0-or-later.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

NAMES = ('requests','echo_replies','buffer_replies','read_replies','writes',
         'time_loads','sat_errors','master_errors','timeouts','fifo_errors',
         'unknown_errors','truncated_errors','buffer_timeouts')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('server','cable','csr-map','output'):p.add_argument('--'+n,required=True)
    p.add_argument('--cycles',type=int,default=3)
    a=p.parse_args()
    if a.cable!='210383B7F02DA':p.error('Only verified Genesys cable is supported')
    if not 1<=a.cycles<=10:p.error('Use 1..10 cycles')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    mapping=json.loads(Path(a.csr_map).read_text())
    if mapping.get('magic')!=0x44525430 or 'packets_alignment' not in mapping['registers']:
        p.error('Requires packet diagnostic CSR map')
    tcl=['lassign $argv server cable','connect -url $server','set matches {}',
         'foreach p [targets -target-properties -filter {name == "PSU"}] {',
         'if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}',
         '}','if {[llength $matches]!=1} {error "Exact Genesys target missing"}',
         'targets -set [lindex $matches 0]','configparams force-mem-accesses 1']
    for name,r in mapping['registers'].items():
        if r['words']!=1:raise ValueError('Single-word registers required')
        tcl.append(f'set addr({name}) {r["address"]}')
    tcl.append('''
proc wr {n v} {global addr; mwr $addr($n) $v}
proc rd {n} {global addr; return [expr {wide([mrd -value $addr($n)])&0xffffffff}]}
proc counts {} {
 set result {}
 foreach n {requests echo_replies buffer_replies read_replies writes time_loads sat_errors master_errors timeouts fifo_errors unknown_errors truncated_errors buffer_timeouts} {dict set result $n [rd packets_$n]}
 return $result
}
proc difference {before after_value} {
 set result {}
 dict for {n v} $before {dict set result $n [expr {([dict get $after_value $n]-$v)&0xffffffff}]}
 return $result
}
proc exercise {command drop expected negative} {
 wr packets_enable 0
 after 25
 wr packets_command $command
 wr packets_drop_reply $drop
 after 25
 wr packets_enable 1
 after 100
 set before [counts]
 after 250
 set after_value [counts]
 set delta [difference $before $after_value]
 set requests [dict get $delta requests]
 if {$requests<500} {error "Too few physical packets command=$command delta=$delta"}
 foreach n $expected {
  set count [dict get $delta $n]
  if {$count<500 || abs($count-$requests)>150} {error "Missing or duplicate command/result $n command=$command delta=$delta"}
 }
 foreach n {sat_errors master_errors fifo_errors timeouts} {
  if {$n eq $negative} {
   if {[dict get $delta $n]<500} {error "Negative control undetected command=$command delta=$delta"}
  } elseif {[dict get $delta $n]!=0} {error "Unexpected errors command=$command delta=$delta"}
 }
 if {$drop && [dict get $delta echo_replies]!=0} {error "Reply suppression failed $delta"}
 wr packets_enable 0
 after 25
 puts "PACKET_RESULT command=$command drop=$drop delta={$delta}"
}
if {[rd monitor_magic]!=0x44525430} {error "Wrong loaded PL; refusing writes"}
wr monitor_tx_enable 0
''')
    tcl.append(f'for {{set cycle 0}} {{$cycle<{a.cycles}}} {{incr cycle}} {{')
    tcl.append('''
 wr monitor_reset 1
 wr monitor_prbs 0
 wr monitor_tx_prbs 0
 wr monitor_loopback 2
 wr packets_enable 0
 wr packets_drop_reply 0
 after 50
 wr monitor_reset 0
 set deadline [expr {[clock milliseconds]+10000}]
 while {1} {
  wr monitor_snapshot 1
  set status [rd monitor_status]
  set alignment [rd packets_alignment]
  if {($status&0x7f)==0x7f && ($alignment&1)} {break}
  if {[clock milliseconds]>$deadline} {error "PHY/aligner timeout status=$status alignment=$alignment"}
  after 50
 }
 after 100
 puts "PACKET_CYCLE cycle=$cycle alignment=$alignment"
 exercise 0 0 {echo_replies} {}
 exercise 1 0 {time_loads} {}
 exercise 2 0 {writes} {}
 exercise 3 0 {buffer_replies} {}
 exercise 4 0 {read_replies} {}
 exercise 5 0 {read_replies} {}
 exercise 6 0 {read_replies} {}
 exercise 0 1 {timeouts} timeouts
 exercise 7 0 {sat_errors buffer_timeouts} sat_errors
 exercise 8 0 {sat_errors unknown_errors} sat_errors
 exercise 9 0 {sat_errors truncated_errors} sat_errors
 exercise 0 0 {echo_replies} {}
}
wr packets_enable 0
wr packets_drop_reply 0
wr monitor_tx_enable 0
puts "TEST ARTIQ_GTH_RT_PACKETS PASS"
puts "TEST EXTERNAL_SATELLITE NOT_RUN"
disconnect
''')
    script=out/'probe.tcl';script.write_text('\n'.join(tcl)+'\n')
    cmd=['vivado-container','shell','-c','exec /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb "$@"','xsdb',str(script.resolve()),a.server,a.cable]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=90+a.cycles*30)
    log=r.stdout+r.stderr;(out/'probe.log').write_text(log)
    ok=r.returncode==0 and 'TEST ARTIQ_GTH_RT_PACKETS PASS' in log
    result={'kind':'physical-hardware','time':time.time(),'status':'PASS' if ok else 'FAIL',
            'scope':'upstream RT request and reply packet engines through time-slotted single GTH PMA loopback; diagnostic CRI backend',
            'cycles':a.cycles,'cable':a.cable,'external_sfp_tx':'disabled',
            'satellite_rtio_execution':'NOT_RUN','aux_firmware':'NOT_RUN',
            'remote_drtio':'NOT_RUN','deterministic_latency':'NOT_RUN',
            'results':[l for l in log.splitlines() if l.startswith(('PACKET_RESULT','PACKET_CYCLE'))],
            'csr_map_sha256':hashlib.sha256(Path(a.csr_map).read_bytes()).hexdigest(),
            'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not ok:print(log[-5000:])
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
