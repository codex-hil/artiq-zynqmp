# SPDX-License-Identifier: LGPL-3.0-or-later
import ctypes,hashlib,struct,subprocess,tempfile,unittest
from pathlib import Path
from test_pit_digest_sleep import Ops,MSR,DISABLE,READ,WRITE,TERM,U
from test_pit_digest_terminal import Record
ROOT=Path(__file__).resolve().parents[1]
class Plan(ctypes.Structure):
 _fields_=[('consumed',U),('nonce',ctypes.c_uint64),('ops',Ops),('ctx',ctypes.c_void_p),('receipt_write',WRITE),('receipt_barrier',DISABLE),('receipt_ctx',ctypes.c_void_p),('image',ctypes.POINTER(U)),('record',Record),('lifecycle',U),('metadata',ctypes.c_int32),('publication',U)]
class Tests(unittest.TestCase):
 def test_same_invocation_binding_and_failure_publication(self):
  with tempfile.TemporaryDirectory() as td:
   base=ROOT/'diagnostics/ddr/pit_collect'
   names=['pit_collect','pit_publish','pit_sample_sha256','pit_capture_digest','pit_digest_sleep','pit_digest_terminal','pit_terminal_build','pit_terminal_record','pit_digest_compose']
   for hashfail in [False,True]:
    sources=[str(base/(n+'.c')) for n in names if not(hashfail and n=='pit_sample_sha256')]
    if hashfail:
     stub=Path(td)/'stub.c';stub.write_text('#include <stdint.h>\nint pit_sample_sha256(const uint32_t *a,uint64_t n,uint32_t *d){(void)a;(void)n;(void)d;return -1;}\n');sources.append(str(stub))
    so=Path(td)/('fail.so' if hashfail else 'real.so');subprocess.run(['cc','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',*sources,'-o',str(so)],check=True)
    fn=ctypes.CDLL(str(so)).pit_digest_compose;fn.argtypes=[ctypes.POINTER(Plan)];fn.restype=ctypes.c_int
    for case_index,case in enumerate(['ok','read-fail','sample-publish-fail','final-fail','initial-fail','receipt-fail']):
     nonce=0x1122334455667700+case_index
     events=[];counts=[0,0];sample=bytearray(48);receipt=bytearray(96);image=(U*8)(*range(1,9))
     @MSR
     def msr(c,out):
      i=counts[0];counts[0]+=1;events.append('msr'+str(i));out[0]=0x102 if i==0 else 0x100
      return -1 if(case=='final-fail' and i==2)or(case=='initial-fail' and i==0) else 0
     @DISABLE
     def disable(c):events.append('disable');return 0
     @READ
     def read(c,a,out):i=counts[1];counts[1]+=1;events.append('read');out[0]=i;return -1 if case=='read-fail' else 0
     @WRITE
     def write(c,o,v):events.append('sample');struct.pack_into('<I',sample,o,v);return -1 if case=='sample-publish-fail' else 0
     @DISABLE
     def fence(c):events.append('fence');return 0
     @TERM
     def terminal(c,s):raise AssertionError('caller terminal must not run')
     @WRITE
     def rw(c,o,v):events.append('receipt');struct.pack_into('<I',receipt,o,v);return -1 if case=='receipt-fail' else 0
     p=Plan();p.nonce=nonce;p.image=image;p.ops=Ops(msr,disable,read,write,fence,terminal);p.receipt_write=rw;p.receipt_barrier=fence
     self.assertEqual(fn(ctypes.byref(p)),0)
     failedhash=hashfail and case not in ['initial-fail','read-fail']
     if failedhash:self.assertEqual(p.metadata,-1);self.assertNotIn('receipt',events);self.assertEqual(bytes(p.record),bytes(96))
     else:
      self.assertEqual(p.metadata,0);self.assertEqual(p.record.nonce,nonce);self.assertEqual(list(p.record.image),list(image));self.assertIn('receipt',events)
      expected=1 if case in ['initial-fail','final-fail'] else 2 if case=='read-fail' else 3 if case=='sample-publish-fail' else 4
      self.assertEqual(p.record.status,expected)
      if case not in ['initial-fail','read-fail']:self.assertEqual(struct.pack('<8I',*p.record.sample),hashlib.sha256(struct.pack('<IIQ8I',1,1,nonce,*range(8))).digest())
      else:self.assertEqual(list(p.record.sample),[0]*8)
      if case!='initial-fail':self.assertLess(events.index('msr2'),events.index('receipt'))
      if case!='receipt-fail':self.assertEqual(receipt,bytes(p.record))
     old=bytes(p);old_events=events[:];self.assertEqual(fn(ctypes.byref(p)),-1);self.assertEqual(bytes(p),old);self.assertEqual(events,old_events)
