# SPDX-License-Identifier: LGPL-3.0-or-later
import ctypes,hashlib,struct,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
U=ctypes.c_uint32
class State(ctypes.Structure):_fields_=[('consumed',U),('valid',U),('digest',U*8)]
READ=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_void_p,U,ctypes.POINTER(U))
WRITE=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_void_p,U,U)
FENCE=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_void_p)
class Tests(unittest.TestCase):
 def test_snapshot_hash_publication_and_failures(self):
  with tempfile.TemporaryDirectory() as td:
   base=ROOT/'diagnostics/ddr/pit_collect';so=Path(td)/'capture.so'
   subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',*[str(base/(n+'.c')) for n in ['pit_collect','pit_publish','pit_sample_sha256','pit_capture_digest']],'-o',str(so)],check=True)
   fn=ctypes.CDLL(str(so)).pit_capture_digest;fn.argtypes=[ctypes.POINTER(State),ctypes.c_uint64,READ,WRITE,FENCE,ctypes.c_void_p];fn.restype=ctypes.c_int
   canonical=struct.pack('<IIQ8I',1,1,7,*range(8))
   for readfail,pubfail in [(None,None)]+[(i,None) for i in range(8)]+[(None,i) for i in range(15)]:
    state=State();mail=bytearray(48);counts=[0,0];errors=[]
    @READ
    def read(ctx,address,out):
     i=counts[0];counts[0]+=1
     if address!=0xffd40044+(i%4)*16:errors.append('address')
     # Nested use must fail before a second read or output mutation.
     if fn(ctypes.byref(state),7,read,write,fence,None)!=0:errors.append('reentry')
     out[0]=i
     return -1 if i==readfail else 0
    def event():
     i=counts[1];counts[1]+=1
     return -1 if i==pubfail else 0
    @WRITE
    def write(ctx,offset,value):
     if not state.valid:errors.append('hash not ready')
     if struct.pack('<8I',*state.digest)!=hashlib.sha256(canonical).digest():errors.append('hash')
     result=event()
     if not result:struct.pack_into('<I',mail,offset,value)
     return result
    @FENCE
    def fence(ctx):return event()
    status=fn(ctypes.byref(state),7,read,write,fence,None)
    self.assertFalse(errors);self.assertEqual(state.consumed,1)
    if readfail is not None:
     self.assertEqual(status,1);self.assertEqual(state.valid,0);self.assertEqual(list(state.digest),[0]*8);self.assertEqual(counts,[readfail+1,0])
    else:
     self.assertEqual(status,3 if pubfail is not None else 4);self.assertEqual(state.valid,1)
     self.assertEqual(struct.pack('<8I',*state.digest),hashlib.sha256(canonical).digest())
     self.assertEqual(counts,[8,pubfail+1 if pubfail is not None else 15])
     if pubfail is None:self.assertEqual(mail,canonical)
    before=bytes(state);oldcounts=counts[:]
    self.assertEqual(fn(ctypes.byref(state),7,read,write,fence,None),0);self.assertEqual(bytes(state),before);self.assertEqual(counts,oldcounts)
   for field in ['consumed','valid','digest']:
    state=State()
    if field=='digest':state.digest[3]=1
    else:setattr(state,field,1)
    before=bytes(state);self.assertEqual(fn(ctypes.byref(state),7,read,write,fence,None),0);self.assertEqual(bytes(state),before)
 def test_hash_failure_without_publication_sanitized(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);base=ROOT/'diagnostics/ddr/pit_collect'
   (p/'main.c').write_text('''#include <assert.h>
#include <stdint.h>
#include "pit_capture_digest.h"
static unsigned reads,publishes;
int pit_sample_sha256(const uint32_t *in,uint64_t nonce,uint32_t *out){(void)out;assert(in[0]==1&&nonce==7);return -1;}
enum pit_publish_status pit_publish(struct pit_attempt *a,const struct pit_record *r,uint64_t n,pit_write_fn w,pit_barrier_fn b,void *c){(void)a;(void)r;(void)n;(void)w;(void)b;(void)c;publishes++;return PIT_CALLBACKS_RETURNED_OFFLINE;}
static int read_value(void *c,uint32_t a,uint32_t *v){(void)c;(void)a;*v=reads++;return 0;}
static int write_value(void *c,uint32_t a,uint32_t v){(void)c;(void)a;(void)v;assert(0);return 0;}
static int barrier(void *c){(void)c;assert(0);return 0;}
int main(void){struct pit_digest_attempt s={0};assert(pit_capture_digest(&s,7,read_value,write_value,barrier,0)==PIT_DIGEST_HASH_FAILED);assert(reads==8&&!publishes&&s.consumed&&!s.digest_valid);for(unsigned i=0;i<8;i++)assert(!s.digest_le[i]);return 0;}
''')
   exe=p/'test';subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(base),str(base/'pit_collect.c'),str(base/'pit_capture_digest.c'),str(p/'main.c'),'-o',str(exe)],check=True,capture_output=True)
   subprocess.run([str(exe)],check=True,capture_output=True)
