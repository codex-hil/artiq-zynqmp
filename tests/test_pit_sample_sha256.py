# SPDX-License-Identifier: LGPL-3.0-or-later
import ctypes,hashlib,random,struct,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def test_fixed_records_against_hashlib_and_rejections(self):
  with tempfile.TemporaryDirectory() as td:
   so=Path(td)/'sha.so';source=ROOT/'diagnostics/ddr/pit_collect/pit_sample_sha256.c'
   subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',str(source),'-o',str(so)],check=True)
   fn=ctypes.CDLL(str(so)).pit_sample_sha256;ptr=ctypes.POINTER(ctypes.c_uint32)
   fn.argtypes=[ptr,ctypes.c_uint64,ptr];fn.restype=ctypes.c_int
   rng=random.Random(98731)
   for i in range(258):
    nonce=rng.randrange(1,2**64);values=[rng.getrandbits(32) for _ in range(8)]
    if i<2:values=[i*0xffffffff]*8
    raw=struct.pack('<IIQ8I',1,1,nonce,*values);words=(ctypes.c_uint32*12)(*struct.unpack('<12I',raw));out=(ctypes.c_uint32*8)(*([0xdeadbeef]*8))
    self.assertEqual(fn(words,nonce,out),0)
    self.assertEqual(struct.pack('<8I',*out),hashlib.sha256(raw).digest())
   raw=struct.pack('<IIQ8I',1,1,7,*range(8));words=(ctypes.c_uint32*12)(*struct.unpack('<12I',raw));out=(ctypes.c_uint32*8)(*([123]*8))
   for index in range(4):
    words[index]^=1;self.assertEqual(fn(words,7,out),-1);self.assertEqual(list(out),[123]*8);words[index]^=1
   for inp,nonce,output in [(None,7,out),(words,0,out),(words,8,out),(words,7,None),(words,7,ctypes.cast(words,ptr)),(words,7,ctypes.cast(ctypes.byref(words,4),ptr)),(ctypes.cast(ctypes.byref(words,1),ptr),7,out),(words,7,ctypes.cast(ctypes.byref(out,1),ptr))]:
    before=bytes(words);beforeout=bytes(out);self.assertEqual(fn(inp,nonce,output),-1);self.assertEqual(bytes(words),before);self.assertEqual(bytes(out),beforeout)

 def test_sanitized_host_execution(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);base=ROOT/'diagnostics/ddr/pit_collect'
   (p/'main.c').write_text('#include <assert.h>\n#include <stdint.h>\n#include <stdio.h>\n#include "pit_sample_sha256.h"\nint main(void){uint32_t in[12]={1,1,7,0,0,1,2,3,4,5,6,7},out[8];\nassert(pit_sample_sha256(in,7,out)==0);\nfor(unsigned i=0;i<8;i++)for(unsigned j=0;j<4;j++)printf("%02x",(out[i]>>(8*j))&255u);\nputs("");in[0]=0;assert(pit_sample_sha256(in,7,out)==-1);return 0;}\n')
   exe=p/'test';subprocess.run(['cc','-std=c11','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(base),str(base/'pit_sample_sha256.c'),str(p/'main.c'),'-o',str(exe)],check=True,capture_output=True)
   got=subprocess.check_output([str(exe)],text=True).strip()
   self.assertEqual(got,hashlib.sha256(struct.pack('<IIQ8I',1,1,7,*range(8))).hexdigest())
