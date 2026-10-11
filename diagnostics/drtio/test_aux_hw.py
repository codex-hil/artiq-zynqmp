#!/usr/bin/env python3
"""Bounded physical upstream AUX SRAM/GTH loopback; LGPL-3.0-or-later."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

CABLE='210383B7F02DA'
LOCK=Path.home()/'.cache'/('genesys-'+CABLE+'.lock')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('server','cable','csr-map','output'):p.add_argument('--'+n,required=True)
    p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    if a.cable!=CABLE:p.error('Only verified Genesys cable is supported')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    mapping=json.loads(Path(a.csr_map).read_text())
    if mapping.get('magic')!=0x44525430 or 'aux_bridge_busy' not in mapping['registers']:
        p.error('AUX diagnostic map required')
    tcl=['lassign $argv server cable','connect -url $server','set matches {}',
         'foreach p [targets -target-properties -filter {name == "PSU"}] {',
         'if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}',
         '}','if {[llength $matches]!=1} {error "Exact Genesys target missing"}',
         'targets -set [lindex $matches 0]','configparams force-mem-accesses 1']
    for name,r in mapping['registers'].items():
        if r['words']!=1:raise ValueError('Single-word registers required')
        tcl.append(f'set addr({name}) {r["address"]}')
    tcl.append(f'set memory {mapping["aux_sram"]["base"]}')
    tcl.append('''
proc wr {n v} {global addr; mwr $addr($n) $v}
proc rd {n} {global addr; return [expr {wide([mrd -value $addr($n)])&0xffffffff}]}
proc wait_value {n value} {
 set limit [expr {[clock milliseconds]+10000}]
 while {[rd $n]!=$value} {
  if {[clock milliseconds]>$limit} {error "Timeout $n expected=$value"}
  after 2
 }
}
proc pattern {number word} {return [expr {((($number+1)*0x01020304)^($word*0x07654321))&0xffffffff}]}
proc send {number words} {
 global memory
 wait_value aux_aux_tx 0
 wait_value aux_bridge_busy 0
 for {set i 0} {$i<$words} {incr i} {mwr [expr {$memory+4*$i}] [pattern $number $i]}
 wr aux_aux_tx_length [expr {$words*4}]
 if {[rd aux_aux_tx_length]!=$words*4} {error "Length readback mismatch"}
 wr aux_aux_tx 1
 wait_value aux_aux_tx 0
 wait_value aux_bridge_busy 0
 after 2
}
proc receive {number words} {
 global memory
 wait_value aux_aux_rx_present 1
 set pointer [rd aux_aux_read_pointer]
 for {set i 0} {$i<$words} {incr i} {
  set actual [expr {wide([mrd -value [expr {$memory+8192+1024*$pointer+4*$i}]])&0xffffffff}]
  if {$actual!=[pattern $number $i]} {error "Payload mismatch number=$number word=$i actual=$actual pointer=$pointer"}
 }
 wr aux_aux_rx_present 1
 after 2
 return $pointer
}
proc reset_link {} {
 wr monitor_reset 1
 wr monitor_prbs 0
 wr monitor_tx_prbs 0
 wr monitor_loopback 2
 after 50
 wr monitor_reset 0
 wait_value aux_in_reset 0
 wait_value aux_rx_up 1
 after 25
 if {[rd aux_aux_rx_present]!=0 || [rd aux_aux_rx_error]!=0} {error "Dirty ring after reset"}
}
if {[rd monitor_magic]!=0x44525430} {error "Wrong PL, refusing writes"}
wr monitor_tx_enable 0
for {set cycle 0} {$cycle<3} {incr cycle} {
 reset_link
 for {set n 0} {$n<10} {incr n} {
  set words [lindex {1 3 17 256} [expr {$n%4}]]
  send $n $words
  set pointer [receive $n $words]
  if {$pointer!=$n%8} {error "Ring pointer mismatch"}
  if {[rd aux_aux_rx_error]!=0 || [rd aux_aux_rx_present]!=0} {error "Unexpected RX error/extra packet"}
  puts "AUX_RESULT cycle=$cycle case=packet words=$words pointer=$pointer"
 }
 for {set n 0} {$n<8} {incr n} {send [expr {$n+100}] 1}
 wait_value aux_aux_rx_error 1
 for {set n 0} {$n<7} {incr n} {receive [expr {$n+100}] 1}
 if {[rd aux_aux_rx_present]!=0} {error "Overflow ring failed to drain"}
 wr aux_aux_rx_error 1
 after 2
 if {[rd aux_aux_rx_error]!=0} {error "RX error failed to clear"}
 send 200 3
 receive 200 3
 if {[rd aux_aux_rx_error]!=0 || [rd aux_aux_rx_present]!=0} {error "Overflow recovery failed"}
 puts "AUX_RESULT cycle=$cycle case=overflow_recovery PASS"
}
wr monitor_tx_enable 0
puts "TEST ARTIQ_GTH_AUX PASS"
disconnect
''')
    script=out/'probe.tcl';script.write_text('\n'.join(tcl)+'\n')
    if a.dry_run:
        print('TCL_GENERATION_ONLY_NOT_HARDWARE',script)
        return 0
    inherited=os.environ.get('GENESYS_LEASE_FD')
    lease=None
    if inherited:
        fd=int(inherited)
        if os.fstat(fd).st_ino!=LOCK.stat().st_ino:raise RuntimeError('Wrong inherited board lock')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    else:
        lease=LOCK.open('a')
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cmd=['vivado-container','shell','-c','exec /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb "$@"','xsdb',str(script.resolve()),a.server,a.cable]
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=300)
        log=r.stdout+r.stderr;(out/'probe.log').write_text(log)
        ok=r.returncode==0 and 'TEST ARTIQ_GTH_AUX PASS' in log
        result={'kind':'physical-hardware','status':'PASS' if ok else 'FAIL','time':time.time(),
                'scope':'upstream AUX SRAM and raw20 framing through single GTH PMA loopback',
                'results':[line for line in log.splitlines() if line.startswith('AUX_RESULT')],
                'external_sfp_tx':'disabled','firmware_aux':'NOT_RUN','active_transfer_reset':'NOT_RUN',
                'csr_map_sha256':hashlib.sha256(Path(a.csr_map).read_bytes()).hexdigest(),
                'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
        if not ok:print(log[-5000:])
        return 0 if ok else 1
    finally:
        if lease:lease.close()


if __name__=='__main__':raise SystemExit(main())
