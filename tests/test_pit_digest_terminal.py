# SPDX-License-Identifier: LGPL-3.0-or-later
import ctypes,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];U=ctypes.c_uint32
class State(ctypes.Structure):_fields_=[('consumed',U),('valid',U),('digest',U*8)]
class Obs(ctypes.Structure):_fields_=[('called',U),('returns',ctypes.c_int32*3),('msr',U*3),('outcome',U)]
class Record(ctypes.Structure):_fields_=[('commit',U),('magic',U),('version',U),('status',U),('nonce',ctypes.c_uint64),('checked',U),('final',U),('image',U*8),('sample',U*8)]
class Tests(unittest.TestCase):
 def test_status_digest_and_rejection_without_output_changes(self):
  with tempfile.TemporaryDirectory() as td:
   base=ROOT/'diagnostics/ddr/pit_collect';so=Path(td)/'terminal.so'
   subprocess.run(['cc','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',str(base/'pit_digest_terminal.c'),str(base/'pit_terminal_build.c'),'-o',str(so)],check=True)
   fn=ctypes.CDLL(str(so)).pit_digest_terminal;fn.argtypes=[ctypes.POINTER(Record),ctypes.POINTER(State),ctypes.c_int,ctypes.POINTER(Obs),ctypes.c_uint64,ctypes.POINTER(U)]
   image=(U*8)(*range(1,9))
   for outcome in range(1,5):
    state=State();state.consumed=1;state.valid=int(outcome>=3)
    if state.valid:state.digest[:]=range(11,19)
    obs=Obs(7,(ctypes.c_int32*3)(0,0,0),(U*3)(0x102,0x100,0x100),outcome)
    if outcome==1:obs.msr[2]=0
    rec=Record();self.assertEqual(fn(ctypes.byref(rec),ctypes.byref(state),outcome,ctypes.byref(obs),7,image),0)
    self.assertEqual((rec.commit,rec.version,rec.status,rec.nonce),(1,1,outcome,7));self.assertEqual(list(rec.sample),list(state.digest))
    # Model/state/result disagreement must not leave a partly built receipt.
    for wrong in [0,5,6,2 if outcome!=2 else 4]:
     out=Record();before=bytes(out);self.assertEqual(fn(ctypes.byref(out),ctypes.byref(state),wrong,ctypes.byref(obs),7,image),-1);self.assertEqual(bytes(out),before)
    before=bytes(rec);self.assertEqual(fn(ctypes.byref(rec),ctypes.byref(state),outcome,ctypes.byref(obs),7,image),-1);self.assertEqual(bytes(rec),before)
    state.valid^=1;out=Record();self.assertEqual(fn(ctypes.byref(out),ctypes.byref(state),outcome,ctypes.byref(obs),7,image),-1);self.assertEqual(bytes(out),bytes(96))
