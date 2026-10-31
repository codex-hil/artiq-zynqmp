# SPDX-License-Identifier: LGPL-3.0-or-later
import ctypes,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from pit_exception_receipt import encode,decode
U=ctypes.c_uint32;PTR=ctypes.POINTER(U)
WRITE=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_void_p,U,U);FENCE=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_void_p)
class Tests(unittest.TestCase):
 def test_host_format_and_all_publication_failure_stages(self):
  with tempfile.TemporaryDirectory() as td:
   so=Path(td)/'fault.so';base=ROOT/'diagnostics/ddr/pit_collect'
   subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',str(base/'pit_fault_record.c'),'-o',str(so)],check=True)
   lib=ctypes.CDLL(str(so));fmt=lib.pit_fault_format;fmt.argtypes=[PTR,U,U,PTR];pub=lib.pit_fault_publish;pub.argtypes=[PTR,PTR,WRITE,FENCE,ctypes.c_void_p]
   for route in (1,2):
    for mask in range(16):
     values=[0x100+i if mask&(1<<i) else 0 for i in range(4)];words=(U*16)();regs=(U*4)(*values)
     self.assertEqual(fmt(words,route,mask,regs),0);raw=struct.pack('<16I',*words)
     self.assertEqual(raw,encode(route,{n:values[i] for i,n in enumerate(['msr','esr','ear','edr']) if mask&(1<<i)}));self.assertFalse(decode(raw)['session_bound'])
   good=(U*16)(*struct.unpack('<16I',encode(2,{'msr':0x100})))
   for fail in [None]+list(range(19)):
    source=(U*16)(*good);state=U();events=[];mail=bytearray(64)
    def event(kind,offset=None,value=None):
     i=len(events);events.append((kind,offset,value))
     # Publisher must already own a snapshot before any callback.
     source[1]=0
     return -1 if i==fail else 0
    @WRITE
    def write(c,o,v):
     r=event('write',o,v)
     if not r:struct.pack_into('<I',mail,o,v)
     return r
    @FENCE
    def fence(c):return event('barrier')
    status=pub(ctypes.byref(state),source,write,fence,None)
    self.assertEqual(status,2 if fail is None else 1);self.assertEqual(state.value,1);self.assertEqual(len(events),19 if fail is None else fail+1)
    if fail is None:self.assertEqual(mail,struct.pack('<16I',*good))
    old=events[:];self.assertEqual(pub(ctypes.byref(state),good,write,fence,None),0);self.assertEqual(events,old)
   out=(U*16)();regs=(U*4)(1,0,0,0)
   self.assertEqual(fmt(out,1,0,regs),-1);self.assertEqual(list(out),[0]*16)
   for index in range(16):
    bad=(U*16)(*good);bad[index]^=0x10 if index==4 else 1
    # Valid snapshot words may vary, other structural corruption must reject.
    if index in (3,5):continue
    state=U();events=[];self.assertEqual(pub(ctypes.byref(state),bad,write,fence,None),0);self.assertFalse(events);self.assertEqual(state.value,0)
 def test_sanitized_formatter_and_publication(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);base=ROOT/'diagnostics/ddr/pit_collect'
   (p/'main.c').write_text('''#include <assert.h>
#include <stdint.h>
#include "pit_fault_record.h"
static uint32_t source[16],mail[16];static unsigned events;
static int write_value(void *c,uint32_t o,uint32_t v){(void)c;assert(o<64&&!(o&3));source[1]=0;mail[o/4]=v;events++;return 0;}
static int barrier(void *c){(void)c;events++;return 0;}
int main(void){uint32_t r[4]={0x100,0,0,0},out[16]={0};struct pit_attempt a={0};assert(pit_fault_format(out,2,1,r)==0);for(unsigned i=0;i<16;i++)source[i]=out[i];assert(pit_fault_publish(&a,source,write_value,barrier,0)==PIT_CALLBACKS_RETURNED_OFFLINE);assert(events==19&&a.consumed);for(unsigned i=0;i<16;i++)assert(mail[i]==out[i]);assert(pit_fault_publish(&a,out,write_value,barrier,0)==PIT_PUBLISH_REJECTED);return 0;}
''')
   exe=p/'test';subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(base),str(base/'pit_fault_record.c'),str(p/'main.c'),'-o',str(exe)],check=True,capture_output=True);subprocess.run([str(exe)],check=True,capture_output=True)
