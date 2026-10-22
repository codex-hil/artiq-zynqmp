"""FSBL instrumentation/strict log controls; LGPL-3.0-or-later."""
import re,subprocess,sys,tempfile,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
from instrument_fsbl_spd import instrument
from decode_fsbl_spd_log import extract
from test_ddr4_spd_crc import fixture

class FSBLSPD(unittest.TestCase):
    def emitted_log(self):
        raw=(REPO/'boards/genesys_zu-5ev/3_bootable/xfsbl_ddr_init.c').read_bytes()
        patched=instrument(raw).decode()
        self.assertEqual(re.findall(r'XIicPs_\w+\(',patched),re.findall(r'XIicPs_\w+\(',raw.decode()))
        body=patched[patched.index('    /* Diagnostic UART only:'):patched.index('\t/* ZCU102,')]
        c='#include <stdio.h>\ntypedef unsigned int u32;\n#define DEBUG_GENERAL 0\n#define XFsbl_Printf(level,...) printf(__VA_ARGS__)\nint main(void){unsigned char SpdData[128]={'+','.join(map(str,fixture()))+'};\n'+body+'puts("Exit from FSBL");}\n'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'emit.c').write_text(c)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'emit.c'),'-o',str(p/'emit')],check=True)
            return subprocess.run([str(p/'emit')],capture_output=True,text=True,check=True).stdout
    def test_actual_injected_c_output_decodes(self):
        data,report=extract(self.emitted_log());self.assertEqual(data,fixture());self.assertEqual(report['geometry']['module_bytes'],4*1024**3)
        self.assertFalse(report['destructive_test_allowed'])
    def test_truncation_duplicate_offset_bad_crc_and_missing_completion(self):
        text=self.emitted_log()
        variants=[text.replace('SPD_BASE_END',''),text+text,text.replace('SPD_BASE 016','SPD_BASE 000'),text.replace('SPD_BASE 000 23','SPD_BASE 000 22'),text.replace('Exit from FSBL','training failed')]
        for value in variants:
            with self.assertRaises(ValueError):extract(value)
    def test_changed_original_source_rejected(self):
        with self.assertRaises(ValueError):instrument(b'changed')

if __name__=='__main__':unittest.main()
