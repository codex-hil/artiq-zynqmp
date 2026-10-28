"""Integrated RO context coupled to real C status pipeline. LGPL-3.0-or-later."""
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'diagnostics/ddr'))
from pit_terminal_receipt import accept


class Tests(unittest.TestCase):
    def test_integrated_ro_context_and_reused_adapter_rejection(self):
        base=ROOT/'diagnostics/ddr/pit_collect'
        with tempfile.TemporaryDirectory() as directory:
            for flags in (['-O2'],['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']):
                exe=Path(directory)/'ro-composition'
                sources=['pit_collect','pit_publish','pit_capture','pit_sleep_model','pit_terminal_record','pit_terminal_build','pit_status_compose','pit_ro_adapter']
                subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',*flags,'-I'+str(base),
                    *[str(base/(n+'.c')) for n in sources],str(ROOT/'tests/fixtures/pit_ro_context_host.c'),'-o',str(exe)],check=True)
                data=subprocess.check_output([str(exe)],timeout=5)
                self.assertEqual(len(data),9*144)
                for i in range(9):
                    pair=data[i*144:(i+1)*144];sample=pair[:48] if i==0 else None;receipt=pair[48:]
                    result=accept(receipt,receipt,7,hashlib.sha256(b'fake-c-trace-image').hexdigest(),sample)
                    self.assertEqual(result['status'],'CAPTURE_COMPLETE' if i==0 else 'READ_FAILED')
                    self.assertFalse(result['sleep_proven'])
                    self.assertFalse(result['destructive_test_allowed'])
                    if i:self.assertEqual(pair[:48],bytes(48))


if __name__=='__main__':unittest.main()
