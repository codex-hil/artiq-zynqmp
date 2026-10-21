"""Exclusive Trenz session and USER2 SPI mailbox. No implicit DAC/HMC writes."""
import fcntl,subprocess,time,re,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
AMD='/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/'
class Session:
 def __enter__(self):
  self.lock=(Path.home()/'.cache/trenz-2516330027B9A.lock').open('a+');fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  self.base=['docker','-H','unix:///run/user/1001/docker-vivado.sock']
  self.cid=subprocess.check_output(self.base+['run','--rm','-d','--mount','type=bind,src=/dev/bus/usb,dst=/dev/bus/usb','--mount','type=bind,src=/home/codex-hil,dst=/home/codex-hil','--mount','type=bind,src=/srv/codex-hil-data,dst=/srv/codex-hil-data','codex-vivado-runtime:ubuntu22.04',AMD+'hw_server','-e','set jtag-port-filter 2516330027B9A'],text=True).strip();time.sleep(3);return self
 def __exit__(self,*args):
  subprocess.run(self.base+['stop',self.cid],capture_output=True,timeout=15);self.lock.close()
 def tool(self,name,text,label):
  t=ROOT/(label+'.tcl');t.write_text(text)
  res=subprocess.run(self.base+['exec',self.cid,AMD+name]+(['-mode','batch','-nojournal','-nolog','-source'] if name=='vivado' else [])+[str(t)],capture_output=True,text=True,timeout=120)
  (ROOT/(label+'.log')).write_text(res.stdout+res.stderr)
  if res.returncode:raise RuntimeError(label+' failed: '+(res.stdout+res.stderr)[-1600:])
  return res.stdout
 def program(self,bit,label='console-program'):
  self.tool('vivado','open_hw_manager\nconnect_hw_server -url localhost:3121\nset ts [get_hw_targets -filter {NAME =~ *2516330027B9A}]\nif {[llength $ts]!=1} {error "Cable mismatch"}\ncurrent_hw_target [lindex $ts 0]\nopen_hw_target\nset ds [get_hw_devices -filter {PART == xczu4}]\nif {[llength $ds]!=1} {error "Device mismatch"}\nset d [lindex $ds 0]\nset_property PROGRAM.FILE '+str(bit)+' $d\nprogram_hw_devices $d\nclose_hw_target\ndisconnect_hw_server\nclose_hw_manager\n',label)
 def run(self,ops,label='console-ops'):
  text='''connect -url tcp:localhost:3121
set ms [jtag targets -target-properties -filter {jtag_cable_serial == "2516330027B9A" && name == "xczu4"}]
if {[llength $ms]!=1} {error "Trenz not found"}
set p [lindex $ms 0]
if {[dict get $p idcode] ne "04721093"} {error "ID mismatch"}
jtag targets [dict get $p node_id]
set sq [jtag sequence]
proc snapshot {} {
 global sq
 $sq clear
 $sq irshift -state IDLE -integer 12 2307
 $sq drshift -state IDLE -capture -tdi 0 128
 set h [lindex [$sq run -hex] 0]
 binary scan [binary format H* $h] i4 words
 if {[lindex $words 3] != 0x53504952} {error "SPI mailbox marker mismatch $h"}
 return $words
}
set initial [snapshot]
set seqnum [expr {[lindex $initial 1]&65535}]
proc spi {command} {
 global sq seqnum
 set seqnum [expr {($seqnum+1)&65535}]
 set packet [expr {(0x53504943<<96)|($seqnum<<32)|$command}]
 $sq clear
 $sq irshift -state IDLE -integer 12 2307
 $sq drshift -state IDLE -integer 128 $packet
 $sq run
 for {set i 0} {$i<20} {incr i} {
  after 3
  set v [snapshot]
  set flags [lindex $v 0]
  if {([lindex $v 1]&65535)==$seqnum && !($flags&256)} {
   if {$flags&1024} {error "SPI engine error flags=$flags"}
   if {[lindex $v 2]!=$command} {error "SPI echo mismatch"}
   return [expr {$flags&255}]
  }
 }
 error "SPI mailbox timeout sequence=$seqnum flags=$flags"
}
'''
  for n,op in enumerate(ops):
   if op[0]=='wait':text+=f'after {op[1]}\n';continue
   if op[0]=='diag':
    text+='''$sq clear
$sq irshift -state IDLE -integer 12 2306
$sq drshift -state IDLE -capture -tdi 0 160
puts "DIAG [lindex [$sq run -hex] 0]"
''';continue
   kind,addr=op[:2]
   if kind=='f':command=0x02000000|addr
   else:
    command=(addr<<8)|((0x800000) if kind=='r' else op[2]);command|=0x1000000 if kind=='h' else 0
   text+=f'puts "SPI {n} {kind} {addr} [spi {command}]"\n'
  text+='''$sq clear
$sq irshift -state IDLE -integer 12 4095
$sq run
$sq delete
disconnect
exit
'''
  out=self.tool('xsdb',text,label);rows=[]
  for n,k,a,v in re.findall(r'SPI (\d+) ([rwhf]) (\d+) (\d+)',out):rows.append({'index':int(n),'kind':k,'address':int(a),'value':int(v)})
  diags=[]
  for h in re.findall(r'DIAG ([0-9a-fA-F]{40})',out):
   v=int.from_bytes(bytes.fromhex(h),'little');assert v>>128==0xfabc204b;diags.append({'ref_count':v&0xffffffff,'sys_count':(v>>32)&0xffffffff,'flags':(v>>64)&0xffffffff,'jesd_count':(v>>96)&0xffffffff})
  return {'operations':rows,'diagnostics':diags}
