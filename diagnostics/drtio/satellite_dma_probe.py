"""Host-armed DDR DMA diagnostic under inherited Genesys lease; LGPL-3.0-or-later.

No loading/reset/flash. Existing external-session parent owns all board leases.
This is NOT native AUX DDMA: host DAP fills DDR and arms the actual PL engine.
"""
import fcntl,hashlib,json,os,re,struct,subprocess
from pathlib import Path

CABLE='210383B7F02DA'
XSDB='/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb'


def abort_trace_bytes():
    """Offline fixture only: exceed the target's 8x128 SED queue capacity.

    No input-gate records: abort resets input control, so the eventual physical
    test must arm observation through packets after recovery, before offset.
    A guarded host-only test may use this 32KiB window (256 bursts). Native
    AUX DDMA remains limited to 1024 payload bytes/16 bursts.
    """
    records=[]
    for i in range(1100):
        records.append(bytes([17,0,0,0])+struct.pack('<Q',1000000+i*16000)+
                       bytes([0])+struct.pack('<I',1-(i%2)))
    return (b''.join(records)+b'\0').ljust(32768,b'\0')


def qualified_dma_shape(qualification):
    """Accept only known routed CDC shapes, including snapshot-enabled target."""
    return (qualification.get('status')=='PASS' and
            (qualification.get('groups'),qualification.get('endpoints')) in
            ((6,164),(8,170)) and qualification.get('requirement_ns')==8 and
            qualification.get('minimum_slack_ns',-1)>=0)


def trace_bytes():
    events=[(1,0,2,3)]
    for i in range(4):
        rise=1000000+i*80000
        events.extend([(0,rise,0,1),(0,rise+8000,0,0)])
    events.append((1,2000000,2,0))
    data=b''.join(bytes([17])+ch.to_bytes(3,'little')+struct.pack('<Q',ts)+bytes([addr])+struct.pack('<I',value)
                  for ch,ts,addr,value in events)+b'\0'
    # Entire bounded read window, including speculative/drain padding.
    return data.ljust(16*128,b'\0')


def make_tcl(mapping,timestamp):
    if not 0<timestamp<2**63 or timestamp%8:
        raise ValueError('Future positive fine3-aligned timestamp required')
    dma=mapping.get('dma')
    if not dma or dma['arena']!={'base':0x22000000,'size':0x200000,'alignment':128}:
        raise ValueError('Expected exclusive diagnostic arena')
    regs=mapping['registers'];lines=[]
    required=('monitor_magic','aux_in_reset','aux_rtio_reset_request','aux_phy_reset_request',
        'aux_rt_reply_fault','aux_rtio_error_flags','aux_rx_up','aux_tsc_load_count',
        'dma_active','dma_clear','dma_accepted','dma_completed','dma_address',
        'dma_time_offset','dma_max_bursts','dma_watchdog','dma_start','dma_pending',
        'dma_reject','dma_result_error')
    if any(name not in regs for name in required):raise ValueError('Incomplete DMA/RTIO map')
    for name,r in regs.items():
        if not re.fullmatch(r'\w+',name):raise ValueError('Invalid CSR name')
        lines.append(f'set addr({name}) {r["address"]}; set words({name}) {r["words"]}')
    lines += ['''proc wr {name value} {
 global addr words
 for {set i 0} {$i<$words($name)} {incr i} {
  mwr [expr {$addr($name)+4*$i}] [expr {($value>>(32*($words($name)-1-$i)))&0xffffffff}]
 }
}
proc rd {name} {
 global addr words
 set value 0
 for {set i 0} {$i<$words($name)} {incr i} {
  set value [expr {($value<<32)|(wide([mrd -value [expr {$addr($name)+4*$i}]])&0xffffffff)}]
 }
 return $value
}
if {[rd monitor_magic]!=0x44525430} {error "Wrong PL identity"}
foreach n {aux_in_reset aux_rtio_reset_request aux_phy_reset_request aux_rt_reply_fault aux_rtio_error_flags dma_active} {
 if {[rd $n]!=0} {error "Unready DMA/RTIO: $n"}
}
if {[rd aux_rx_up]!=1 || [rd aux_tsc_load_count]==0} {error "No external TSC/link"}
wr dma_clear 1
set accepted [rd dma_accepted]
set completed [rd dma_completed]
''']
    data=trace_bytes()
    for i in range(0,len(data),4):
        word=int.from_bytes(data[i:i+4],'little');addr=0x22000000+i
        lines += [f'mwr {addr} {word}',f'if {{(wide([mrd -value {addr}])&0xffffffff)!={word}}} {{error "DDR readback offset {i}"}}']
    lines.append('puts "SATELLITE_DDR_READBACK_PASS bytes=2048 base=570425344"')
    lines += [f'wr dma_address {0x22000000}',f'wr dma_time_offset {timestamp}',
        'wr dma_max_bursts 16','wr dma_watchdog 134217728',
        f'if {{[rd dma_address]!=570425344 || [rd dma_time_offset]!={timestamp} || [rd dma_max_bursts]!=16 || [rd dma_watchdog]!=134217728}} {{error "DMA configuration readback mismatch"}}',
        'puts "SATELLITE_DMA_CONFIG address=[rd dma_address] offset=[rd dma_time_offset] max_bursts=[rd dma_max_bursts] watchdog=[rd dma_watchdog]"',
        'wr dma_start 1','''
set deadline [expr {[clock milliseconds]+3000}]
while {[rd dma_pending]==0} {
 if {[clock milliseconds]>$deadline} {error "DMA completion timeout; restoration required"}
 after 1
}
puts "SATELLITE_DMA_STATUS active=[rd dma_active] pending=[rd dma_pending] reject=[rd dma_reject] error=[rd dma_result_error] channel=[rd dma_result_channel] timestamp=[rd dma_result_timestamp] accepted=[rd dma_accepted] completed=[rd dma_completed] rtio_reset=[rd aux_rtio_reset_applied] phy_reset=[rd aux_phy_reset_applied] errors=[rd aux_rtio_error_flags] reply_fault=[rd aux_rt_reply_fault] loads=[rd aux_tsc_load_count]"
if {[rd dma_active]!=0 || [rd dma_reject]!=0 || [rd dma_result_error]!=0} {error "DMA failed/rejected"}
if {[rd dma_accepted]!=$accepted+1 || [rd dma_completed]!=$completed+1} {error "Missing hardware DMA epoch"}
if {[rd aux_rt_reply_fault]!=0 || [rd aux_rtio_error_flags]!=0} {error "Satellite RTIO fault"}
puts "SATELLITE_DDR_DMA_ADMITTED_PASS bursts_limit=16 readback_bytes=2048"
disconnect
''']
    return '\n'.join(lines)+'\n'


def make_abort_tcl(mapping,timestamp):
    """Host-only abort plan; caller must hold lease and stage exact trace.bin.

    Separate opt-in host-only mode; native AUX DDMA cannot enable this plan.
    """
    regs=mapping.get('registers',{})
    extra=('dma_abort','aux_tsc_snapshot_request','aux_tsc_snapshot_busy',
           'aux_tsc_snapshot_valid','aux_tsc_snapshot_value','aux_rtio_reset_applied',
           'aux_phy_reset_applied')
    if any(n not in regs for n in extra):raise ValueError('Incomplete abort/snapshot map')
    # Reuse exact identity/readiness checks and MSW-first CSR helpers.
    prefix=make_tcl(mapping,timestamp).split('wr dma_clear 1',1)[0]
    return prefix+\
'''
proc binary_read {name} {
 set f [open $name rb];set data [read $f];close $f;return $data
}
proc snapshot {} {
 if {[rd aux_tsc_snapshot_busy]} {error "Snapshot already busy"}
 wr aux_tsc_snapshot_request 1
 set deadline [expr {[clock milliseconds]+1000}]
 while {[rd aux_tsc_snapshot_busy] || ![rd aux_tsc_snapshot_valid]} {
  if {[clock milliseconds]>$deadline} {error "Snapshot timeout"}
 }
 return [rd aux_tsc_snapshot_value]
}
set directory [file dirname [info script]]
set expected [binary_read [file join $directory trace.bin]]
if {[string length $expected]!=32768} {error "Wrong abort fixture size"}
mwr -bin -file [file join $directory trace.bin] 570425344 8192
mrd -bin -file [file join $directory readback.bin] 570425344 8192
if {[binary_read [file join $directory readback.bin]] ne $expected} {error "DDR block readback mismatch"}
wr dma_clear 1
set accepted [rd dma_accepted];set completed [rd dma_completed]
set epoch [rd aux_tsc_load_count]
'''+f'wr dma_address 570425344\nwr dma_time_offset {timestamp}\n'+\
'''wr dma_max_bursts 256
wr dma_watchdog 134217728
if {[rd dma_address]!=570425344 || [rd dma_max_bursts]!=256 || [rd dma_watchdog]!=134217728} {error "Abort configuration mismatch"}
set sampled_at [clock milliseconds]
set sampled [snapshot]
'''+f'set offset {timestamp}\n'+\
'''if {[rd dma_time_offset]!=$offset} {error "Time offset readback mismatch"}
# Conservative age bound: at most2 mu/ns, plus1 second of lead.
if {$sampled+([clock milliseconds]-$sampled_at)*2000000+1000000000 >= $offset} {error "Insufficient future offset"}
wr dma_start 1
after 20
if {[rd dma_accepted]!=$accepted+1 || [rd dma_completed]!=$completed || ![rd dma_active] || [rd dma_pending]} {error "DMA did not remain active before abort"}
if {[rd dma_reject] || [rd dma_result_error]} {error "Unexpected preabort fault"}
puts "SATELLITE_DMA_PREABORT active=[rd dma_active] accepted=[rd dma_accepted] completed=[rd dma_completed] epoch=$epoch sampled=$sampled offset=$offset"
wr dma_abort 1
set deadline [expr {[clock milliseconds]+3000}]
while {[rd dma_active] || ![rd dma_pending]} {
 if {[clock milliseconds]>$deadline} {error "Abort/recovery timeout"}
 after 1
}
if {[rd dma_result_error]!=1 || [rd dma_reject] || [rd dma_accepted]!=$accepted+1 || [rd dma_completed]!=$completed+1} {error "Unexpected abort result"}
foreach n {aux_in_reset aux_rtio_reset_request aux_phy_reset_request aux_rtio_reset_applied aux_phy_reset_applied aux_rt_reply_fault aux_rtio_error_flags} {
 if {[rd $n]} {error "Postabort RTIO fault: $n"}
}
if {[rd aux_rx_up]!=1 || [rd aux_tsc_load_count]!=$epoch} {error "Postabort link/TSC epoch changed"}
if {[snapshot]<=$sampled} {error "TSC did not advance"}
if {$sampled+([clock milliseconds]-$sampled_at)*2000000+1000000000 >= $offset} {error "Abort too late for observation"}
# Keep sticky error/pending, do not clear/restart DMA or reset RTIO.
puts "SATELLITE_DMA_POSTABORT active=[rd dma_active] pending=[rd dma_pending] error=[rd dma_result_error] accepted=[rd dma_accepted] completed=[rd dma_completed] epoch=[rd aux_tsc_load_count]"
puts "SATELLITE_DMA_ABORT_DRAIN_PASS bytes=32768 bursts_limit=256 error=1"
disconnect
'''


def run_probe(config,output,timestamp):
    fd=int(os.environ['GENESYS_LEASE_FD'])
    actual=os.fstat(fd);expected=Path('/home/codex-hil/.cache/genesys-'+CABLE+'.lock').stat()
    if (actual.st_dev,actual.st_ino)!=(expected.st_dev,expected.st_ino):
        raise ValueError('Wrong inherited Genesys lease')
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    c=json.loads(Path(config).read_text());build=Path(c['bitstream']).parent
    q=json.loads((build/'dma-cdc-results.json').read_text())
    if not qualified_dma_shape(q):raise ValueError('DMA implementation unqualified')
    for name,expected_hash in q['sha256'].items():
        if hashlib.sha256((build/name).read_bytes()).hexdigest()!=expected_hash:
            raise ValueError('Stale DMA qualification: '+name)
    mapping=json.loads(Path(c['csr_map']).read_text())
    if Path(c['csr_map']).resolve()!=(build/'csr-map.json').resolve():raise ValueError('Wrong DMA map')
    abort=bool(c.get('host_dma_abort_test',False))
    if abort and (not c.get('host_dma_test') or not c.get('snapshot_test') or c.get('native_ddma_mode') or
                  c.get('abort_acknowledgement')!='host-only-32768-byte-window'):
        raise ValueError('Abort requires reviewed host-only mode, snapshot and explicit window')
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    (out/'trace.bin').write_bytes(abort_trace_bytes() if abort else trace_bytes())
    prefix=['lassign $argv server cable','connect -url $server','set matches {}',
        'foreach p [targets -target-properties -filter {name == "PSU"}] {',
        'if {[dict exists $p jtag_cable_serial] && [dict get $p jtag_cable_serial] eq $cable} {lappend matches [dict get $p target_id]}',
        '}','if {[llength $matches]!=1} {error "Exact Genesys target missing"}',
        'targets -set [lindex $matches 0]','configparams force-mem-accesses 1']
    script=out/'probe.tcl';script.write_text('\n'.join(prefix)+'\n'+
        (make_abort_tcl(mapping,int(timestamp)) if abort else make_tcl(mapping,int(timestamp))))
    r=subprocess.run(['vivado-container','shell','-c','exec "$@"','bash',XSDB,str(script.resolve()),c['server'],CABLE],
        capture_output=True,text=True,timeout=25,pass_fds=(fd,))
    log=r.stdout+r.stderr;(out/'probe.log').write_text(log)
    marker='SATELLITE_DMA_ABORT_DRAIN_PASS' if abort else 'SATELLITE_DDR_DMA_ADMITTED_PASS'
    if r.returncode or marker not in log:
        raise RuntimeError('Host-armed satellite DMA failed; inspect probe.log and restore via parent')
