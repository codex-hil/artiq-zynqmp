# SPDX-License-Identifier: LGPL-3.0-or-later
import ctypes,hashlib,struct,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
U=ctypes.c_uint32;PTR=ctypes.POINTER(U)
MSR=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_void_p,PTR)
DISABLE=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_void_p)
READ=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_void_p,U,PTR)
WRITE=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_void_p,U,U)
TERM=ctypes.CFUNCTYPE(None,ctypes.c_void_p,ctypes.c_int)
class State(ctypes.Structure):_fields_=[('consumed',U),('valid',U),('digest',U*8)]
class Ops(ctypes.Structure):_fields_=[('msr',MSR),('disable',DISABLE),('read',READ),('write',WRITE),('barrier',DISABLE),('terminal',TERM)]
class Tests(unittest.TestCase):
 def test_internal_digest_final_observation_and_rejections(self):
  with tempfile.TemporaryDirectory() as td:
   base=ROOT/'diagnostics/ddr/pit_collect';so=Path(td)/'sleep.so'
   subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',*[str(base/(n+'.c')) for n in ['pit_collect','pit_publish','pit_sample_sha256','pit_capture_digest','pit_digest_sleep']],'-o',str(so)],check=True)
   fn=ctypes.CDLL(str(so)).pit_digest_sleep;fn.argtypes=[ctypes.POINTER(State),ctypes.c_uint64,ctypes.POINTER(Ops),ctypes.c_void_p];fn.restype=ctypes.c_int
   for case in ['ok','initial-fail','after-fail','final-fail','disable-fail','after-drift','final-drift','read-fail','publish-fail']:
    state=State();events=[];counts=[0,0];term=[];nested=[]
    @MSR
    def msr(c,out):
     i=counts[0];counts[0]+=1;events.append('msr'+str(i));out[0]=0x102 if i==0 else 0x100
     if (i==1 and case=='after-drift')or(i==2 and case=='final-drift'):out[0]=0
     nested.append(fn(ctypes.byref(state),7,ctypes.byref(ops),None))
     return -1 if (i==0 and case=='initial-fail')or(i==1 and case=='after-fail')or(i==2 and case=='final-fail') else 0
    @DISABLE
    def disable(c):events.append('disable');return -1 if case=='disable-fail' else 0
    @READ
    def read(c,a,out):i=counts[1];counts[1]+=1;events.append('read');out[0]=i;return -1 if case=='read-fail' else 0
    @WRITE
    def write(c,o,v):events.append('write');return -1 if case=='publish-fail' else 0
    @DISABLE
    def fence(c):events.append('fence');return 0
    @TERM
    def terminal(c,status):events.append('terminal');term.append(status)
    ops=Ops(msr,disable,read,write,fence,terminal)
    result=fn(ctypes.byref(state),7,ctypes.byref(ops),None)
    expected=4 if case=='ok' else 2 if case=='read-fail' else 3 if case=='publish-fail' else 1
    self.assertEqual(result,expected);self.assertEqual(term,[expected]);self.assertTrue(all(x==0 for x in nested));self.assertEqual(events[-1],'terminal')
    if case in ['ok','final-fail','final-drift','read-fail','publish-fail']:
     self.assertEqual(counts[0],3);self.assertEqual(events[-2],'msr2')
    valid=case in ['ok','final-fail','final-drift','publish-fail'];self.assertEqual(state.valid,int(valid))
    if valid:self.assertEqual(struct.pack('<8I',*state.digest),hashlib.sha256(struct.pack('<IIQ8I',1,1,7,*range(8))).digest())
    else:self.assertEqual(list(state.digest),[0]*8)
    before=bytes(state);old=events[:];self.assertEqual(fn(ctypes.byref(state),7,ctypes.byref(ops),None),0);self.assertEqual(bytes(state),before);self.assertEqual(events,old)
 def test_hash_failure_remains_distinct_sanitized(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);base=ROOT/'diagnostics/ddr/pit_collect'
   (p/'main.c').write_text('''#include <assert.h>
#include "pit_digest_sleep.h"
static unsigned observations,terminals;
enum pit_digest_status pit_capture_digest(struct pit_digest_attempt *s,uint64_t n,pit_read_fn r,pit_write_fn w,pit_barrier_fn b,void *c){(void)n;(void)r;(void)w;(void)b;(void)c;s->consumed=1;return PIT_DIGEST_HASH_FAILED;}
static int msr(void *c,uint32_t *v){(void)c;*v=observations++?0x100:0x102;return 0;}
static int disable(void *c){(void)c;return 0;}
static int read_value(void *c,uint32_t a,uint32_t *v){(void)c;(void)a;(void)v;assert(0);return 0;}
static int write_value(void *c,uint32_t a,uint32_t v){(void)c;(void)a;(void)v;assert(0);return 0;}
static void terminal(void *c,int s){(void)c;assert(s==PIT_DS_HASH_FAILED);assert(observations==3);terminals++;}
int main(void){struct pit_digest_attempt state={0};struct pit_sleep_ops ops={msr,disable,read_value,write_value,disable,terminal};assert(pit_digest_sleep(&state,7,&ops,0)==PIT_DS_HASH_FAILED);assert(state.consumed&&!state.digest_valid&&terminals==1);return 0;}
''')
   exe=p/'test';subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(base),str(base/'pit_digest_sleep.c'),str(p/'main.c'),'-o',str(exe)],check=True,capture_output=True);subprocess.run([str(exe)],check=True,capture_output=True)
