#!/usr/bin/env python3
"""Physical PL DDR-reader -> upstream RTIO DMA -> JB1/JB2 test.

Requires DMA PL/PS configuration initialized, CPU1 idle, JB1-JB2 jumper.
No software pulse replay; DAP only fills DDR and starts the FPGA engine.
Not a CoreDMA record/playback API test. No PS/PL reset performed here.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['csr-map','server','cable','output']:p.add_argument('--'+name,required=True)
    o=p.parse_args();out=Path(o.output).resolve();out.mkdir(parents=True,exist_ok=True)
    regs=json.loads(Path(o.csr_map).read_text())['registers']
    events=[(1,0,2,3)] # gate both edges
    for i in range(4):
        rise=1000000+i*25000
        events.extend([(0,rise,0,1),(0,rise+12500,0,0)])
    events.append((1,1200000,2,0))
    trace=b''.join(bytes([17])+channel.to_bytes(3,'little')+struct.pack('<Q',ts)+bytes([addr])+struct.pack('<I',data) for channel,ts,addr,data in events)+b'\0'
    trace+=b'\0'*((-len(trace))%128)
    (out/'trace.bin').write_bytes(trace)
    tcl=['connect -url '+o.server,'set matches {}']
    tcl+=['foreach props [targets -target-properties -filter {name == "PSU"}] {',
          ' if {[dict exists $props jtag_cable_serial] && [dict get $props jtag_cable_serial] eq "'+o.cable+'"} {lappend matches [dict get $props target_id]}','}',
          'if {[llength $matches] != 1} {error "Exact Genesys cable not found"}',
          'targets -set [lindex $matches 0]','configparams force-mem-accesses 1']
    for name,r in regs.items():tcl.append(f'set addr({name}) {r["address"]}; set words({name}) {r["words"]}')
    tcl+=['''proc wr {name value} {
 global addr words
 for {set i 0} {$i < $words($name)} {incr i} {
  set shift [expr {32*($words($name)-1-$i)}]
  mwr [expr {$addr($name)+4*$i}] [expr {($value >> $shift)&0xffffffff}]
 }
}
proc rd {name} {
 global addr words
 set value 0
 for {set i 0} {$i < $words($name)} {incr i} {
  set word [mrd -value [expr {$addr($name)+4*$i}]]
  set value [expr {($value << 32) | (wide($word)&0xffffffff)}]
 }
 return $value
}
proc counter {} {wr rtio_counter_update 1; return [rd rtio_counter]}
wr cri_con_selected 0
wr rtio_core_reset 1
wr rtio_core_reset_phy 1
''']
    for i in range(0,len(trace),4):tcl.append(f'mwr {0x22000000+i} {int.from_bytes(trace[i:i+4],"little")}')
    tcl+=['''set start [expr {[counter]+625000000}]
wr rtio_dma_base_address 0x22000000
wr rtio_dma_time_offset $start
wr cri_con_selected 1
wr rtio_dma_enable 1
set deadline [expr {[clock milliseconds]+3000}]
while {[rd rtio_dma_enable] != 0} {
 if {[clock milliseconds]>$deadline} {error "DMA DDR reader/CRI completion timeout"}
 after 10
}
set bus_error [rd rtio_dma_wb_reader_bus_error]
set dma_error [rd rtio_dma_error]
if {$bus_error || $dma_error} {error "DMA errors AXI=$bus_error RTIO=$dma_error"}
wr cri_con_selected 0
set deadline [expr {[clock milliseconds]+8000}]
while {[counter]<$start+1500000} {
 if {[clock milliseconds]>$deadline} {error "RTIO counter timeout"}
 after 10
}
set stamps {}
for {set i 0} {$i<8} {incr i} {
 wr rtio_target 256
 wr rtio_i_timeout 0
 set status [rd rtio_i_status]
 if {$status != 0} {error "Missing/overflowed physical input edge $i status=$status"}
 lappend stamps [rd rtio_i_timestamp]
}
set latency [expr {[lindex $stamps 0]-$start-1000000}]
if {$latency != 15} {error "Unexpected loopback latency $latency"}
for {set i 0} {$i<8} {incr i} {
 set expected [expr {$start+1000000+($i/2)*25000+($i%2)*12500+15}]
 if {[lindex $stamps $i] != $expected} {error "Physical DMA edge timestamp mismatch $i"}
}
wr rtio_target 256
wr rtio_i_timeout 0
if {[rd rtio_i_status] != 1} {error "Unexpected extra input edge"}
if {[rd rtio_core_async_error] != 0} {error "RTIO asynchronous errors"}
puts "DMA_PHYSICAL_PASS start=$start latency=$latency edges=$stamps"
# Negative control: replay into the past; firmware must not call this success.
wr rtio_dma_time_offset 0
wr cri_con_selected 1
wr rtio_dma_enable 1
set deadline [expr {[clock milliseconds]+3000}]
while {[rd rtio_dma_enable] != 0} {
 if {[clock milliseconds]>$deadline} {error "Underflow drain timeout"}
 after 10
}
wr cri_con_selected 0
if {[rd rtio_dma_wb_reader_bus_error] != 0} {error "Unexpected DDR error"}
if {[rd rtio_dma_error] != 1} {error "Missing real DMA underflow"}
if {[rd rtio_dma_error_channel] != 1 || [rd rtio_dma_error_timestamp] != 0 || [rd rtio_dma_error_address] != 2} {error "DMA underflow metadata mismatch"}
wr rtio_dma_error 1
if {[rd rtio_dma_error] != 0} {error "DMA error acknowledgment failed"}
puts "DMA_UNDERFLOW_PASS channel=1 timestamp=0 address=2 acknowledged=1"
disconnect
''']
    script=out/'probe.tcl';script.write_text('\n'.join(tcl))
    proc=subprocess.run(['vivado-container','shell','-c','exec /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb "$@"','xsdb',str(script)],capture_output=True,text=True,timeout=60)
    log=proc.stdout+proc.stderr;(out/'xsdb.log').write_text(log)
    result={'kind':'hardware','scope':__doc__,'csr_map':o.csr_map,'trace_address':'0x22000000','trace_bytes':len(trace),'status':'PASS' if proc.returncode==0 and 'DMA_PHYSICAL_PASS' in log and 'DMA_UNDERFLOW_PASS' in log else 'FAIL','log':log}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
