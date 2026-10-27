"""Failed callback output is not a successful MSR observation. LGPL-3.0-or-later."""
import hashlib
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'diagnostics/ddr'))
from pit_receipt_producer import ReceiptProducer
from pit_terminal_receipt import accept
IMAGE=b'fake-c-trace-image'


def replay_missing(data):
    if type(data) is not bytes or len(data)!=6*188:raise ValueError('exact six fake observation frames required')
    results=[]
    for mode in range(6):
        frame=data[mode*188:(mode+1)*188]
        magic,version,case,valid,calls,disabled,reads,status,*raw=struct.unpack('<11I',frame[:44])
        expected=[(0,1,0,0),(1,1,1,0),(1,2,1,0),(3,3,1,8),(3,2,1,0),(7,3,1,8)][mode]
        if (magic,version,case)!=(0x504d4f31,1,mode) or (valid,calls,disabled,reads)!=expected:
            raise ValueError('invalid fake lifecycle event sequence/validity')
        observations=[value if valid&(1<<i) else None for i,value in enumerate(raw)]
        producer=ReceiptProducer(IMAGE,7);producer.checked_irq(*observations[:2])
        sample=frame[44:92] if reads else None
        producer.sample_result('COMPLETE' if reads else 'IRQ_UNPROVEN',sample)
        derived=producer.finish(observations[2])
        if derived!=frame[92:] or struct.unpack_from('<I',derived,12)[0]!=status:
            raise ValueError('receipt inconsistent with valid observations')
        results.append(accept(derived,derived,7,hashlib.sha256(IMAGE).hexdigest(),sample))
    return results


class Tests(unittest.TestCase):
    def test_real_c_failures_and_validity_promotion_negatives(self):
        base=ROOT/'diagnostics/ddr/pit_collect'
        with tempfile.TemporaryDirectory() as directory:
            for flags in (['-O2'],['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']):
                exe=Path(directory)/'missing'
                subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',*flags,'-I'+str(base),
                    *[str(base/(n+'.c')) for n in ['pit_collect','pit_publish','pit_capture','pit_sleep_model','pit_terminal_record']],
                    str(ROOT/'tests/fixtures/pit_missing_observation_host.c'),'-o',str(exe)],check=True)
                data=subprocess.check_output([str(exe)],timeout=5)
                results=replay_missing(data)
                self.assertEqual([r['status'] for r in results],['IRQ_UNPROVEN']*5+['CAPTURE_COMPLETE'])
                self.assertTrue(all(not r['sleep_proven'] for r in results))
                for mode in range(5):
                    changed=bytearray(data);changed[mode*188+12]|=7
                    with self.assertRaises(ValueError):replay_missing(bytes(changed))
                # Poisoning data returned by a FAILED read cannot change derived receipt.
                changed=bytearray(data);struct.pack_into('<I',changed,32,0xdeadbeef)
                self.assertEqual(replay_missing(bytes(changed))[0]['status'],'IRQ_UNPROVEN')
                with self.assertRaises(ValueError):replay_missing(data[:-1])


if __name__=='__main__':unittest.main()
