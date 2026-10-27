"""Real C lifecycle/writer composition with Python binding checks. LGPL-3.0-or-later."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'diagnostics/ddr'))
from pit_terminal_receipt import accept


class Tests(unittest.TestCase):
    def test_composed_faults_and_cross_language_receipts(self):
        base=ROOT/'diagnostics/ddr/pit_collect'
        with tempfile.TemporaryDirectory() as directory:
            for flags in (['-O2'],['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']):
                exe=Path(directory)/'coupled'
                sources=['pit_collect','pit_publish','pit_capture','pit_sleep_model','pit_terminal_record']
                subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',*flags,'-I'+str(base),
                                *[str(base/(name+'.c')) for name in sources],
                                str(ROOT/'tests/fixtures/pit_status_coupling_host.c'),'-o',str(exe)],check=True)
                data=subprocess.check_output([str(exe)],timeout=5)
                self.assertEqual(len(data),5*144)
                for index,status in enumerate(['CAPTURE_COMPLETE','READ_FAILED','PUBLICATION_UNKNOWN','IRQ_UNPROVEN','CAPTURE_COMPLETE']):
                    pair=data[index*144:(index+1)*144];sample=pair[:48];receipt=pair[48:]
                    result=accept(receipt,receipt,7,'12'*32,sample if index!=1 else None)
                    self.assertEqual(result['status'],status)
                    self.assertFalse(result['sleep_proven'])
                    self.assertFalse(result['destructive_test_allowed'])
                    self.assertEqual(result['samples'] is not None,index in (0,4))


if __name__=='__main__':unittest.main()
