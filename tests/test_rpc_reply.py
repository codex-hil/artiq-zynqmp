"""Real pinned host serializer versus extracted C parser; LGPL-3.0-or-later."""
import json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'common/artiq'))
from artiq.coredevice.comm_kernel import CommKernel


class ReplyParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name);src=root/'probe.c'
        src.write_text('''#include <stdio.h>
#include "rpc_reply.h"
int main(void) {
 struct genesys_rpc_reply p;genesys_rpc_reply_init(&p);int c,r=0;
 while((c=getchar())!=EOF) {r=genesys_rpc_reply_byte(&p,(uint8_t)c);if(r<0)break;}
 printf("%d:",r);if(r==1)for(size_t i=0;i<p.expected;i++)printf("%02x",p.payload[i]);
 return 0;
}
''')
        cls.probe=root/'probe'
        subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I',str(REPO/'boards/genesys_zu-5ev/2_firmware_a53/c'),str(src),'-o',str(cls.probe)],check=True)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def wire(self,tag,value):
        c=CommKernel('unused');c.pack_int8=struct.Struct('<B').pack;c.pack_int32=struct.Struct('<l').pack;c.pack_int64=struct.Struct('<q').pack;c.pack_float64=struct.Struct('<d').pack
        c._write_bytes(tag)
        c._send_rpc_value(bytearray(tag),value,value,self.wire)
        return bytes(c.write_buffer)

    def parse(self,data):
        return subprocess.run([str(self.probe)],input=data,capture_output=True,check=True).stdout.decode()

    def test_real_host_scalar_values_and_every_truncated_prefix(self):
        for tag,value in [(b'n',None),(b'b',False),(b'b',True),(b'i',-2**31),(b'i',2**31-1),(b'I',-2**63),(b'I',2**63-1),(b'f',3.75),(b'f',float('inf'))]:
            with self.subTest(tag=tag,value=value):
                data=self.wire(tag,value)
                self.assertEqual(self.parse(data),'1:'+data[5:].hex())
                for end in range(len(data)):self.assertEqual(self.parse(data[:end]),'0:')
                self.assertEqual(self.parse(data+b'extra'),'-1:')

    def test_bad_length_tags_and_explicit_reset(self):
        for n in (0,2,0xffffffff,0x80000001):self.assertEqual(self.parse(struct.pack('<I',n)+b'i'),'-1:')
        for tag in (b't',b'l',b's',b'?',b'\0'):self.assertEqual(self.parse(struct.pack('<I',1)+tag),'-1:')
        # Separate fresh session after invalid input must still accept real host data.
        self.assertEqual(self.parse(self.wire(b'i',42)),'1:2a000000')

if __name__=='__main__':unittest.main()
