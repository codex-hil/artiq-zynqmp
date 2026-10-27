"""C fake-callback event trace -> derived receipt crosscheck. LGPL-3.0-or-later."""
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


def replay(data,image=IMAGE):
    if type(data) is not bytes or len(data)!=5*188:
        raise ValueError('exact five fake-C event frames required')
    results=[]
    for mode in range(5):
        frame=data[mode*188:(mode+1)*188]
        magic,version,case,count,before,checked,final,outcome,lifecycle,publication,post=struct.unpack('<11I',frame[:44])
        if (magic,version,case,count)!=(0x50544531,1,mode,3) or outcome not in (2,3,4) or publication!=2:
            raise ValueError('inconsistent fake trace frame')
        sample=frame[44:92] if outcome!=2 else None
        producer=ReceiptProducer(image,7);producer.checked_irq(before,checked)
        producer.sample_result({2:'READ_FAILED',3:'PUBLICATION_UNKNOWN',4:'COMPLETE'}[outcome],sample)
        derived=producer.finish(final);supplied=frame[92:]
        if derived!=supplied or struct.unpack_from('<I',derived,12)[0]!=lifecycle:
            raise ValueError('derived receipt differs from C events/bytes')
        # The image digest is derived by producer, not supplied by trace fields.
        import hashlib
        result=accept(derived,derived,7,hashlib.sha256(image).hexdigest(),sample)
        results.append((result,post,final))
    return results


class Tests(unittest.TestCase):
    def test_c_trace_and_mutation_controls(self):
        base=ROOT/'diagnostics/ddr/pit_collect'
        with tempfile.TemporaryDirectory() as directory:
            for flags in (['-O2'],['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer']):
                exe=Path(directory)/'events'
                subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-DPIT_EVENT_TRACE=1',*flags,
                    '-I'+str(base),*[str(base/(name+'.c')) for name in ['pit_collect','pit_publish','pit_capture','pit_sleep_model','pit_terminal_record']],
                    str(ROOT/'tests/fixtures/pit_status_coupling_host.c'),'-o',str(exe)],check=True)
                data=subprocess.check_output([str(exe)],timeout=5)
                results=replay(data)
                self.assertEqual([r[0]['status'] for r in results],['CAPTURE_COMPLETE','READ_FAILED','PUBLICATION_UNKNOWN','IRQ_UNPROVEN','CAPTURE_COMPLETE'])
                self.assertTrue(all(not r[0]['sleep_proven'] for r in results))
                self.assertNotEqual(results[4][1],results[4][2]) # Post-snapshot IRQ drift remains outside receipt.
                for offset in [0,4,8,12,24,28,32,44,92,124,156,188*3+24]:
                    changed=bytearray(data);changed[offset]^=1
                    with self.assertRaises(ValueError):replay(bytes(changed))
                with self.assertRaises(ValueError):replay(data,image=IMAGE+b'wrong')
                with self.assertRaises(ValueError):replay(data[:-1])


if __name__=='__main__':unittest.main()
