"""Check upstream analyzer wire records, ring wrap, stop and capture restart."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"boards/genesys_zu-5ev/1_gateware"))
from types import SimpleNamespace
from migen import Signal
from migen.sim import run_simulation
from artiq.gateware.rtio.cri import Interface,commands
from artiq.coredevice.comm_analyzer import decode_message,OutputMessage,StoppedMessage
from analyzer_bram import AnalyzerBRAM

class AnalyzerTest(unittest.TestCase):
    def test_records_wrap_and_restart(self):
        cri=Interface();tsc=SimpleNamespace(full_ts_cri=Signal(64))
        d=AnalyzerBRAM(tsc,cri,depth=4)
        def run():
            for i in range(6):
                yield cri.cmd.eq(commands['write'])
                yield cri.chan_sel.eq(i%2)
                yield cri.o_timestamp.eq(100+i)
                yield cri.o_data.eq(10+i)
                yield tsc.full_ts_cri.eq(50+i)
                yield
            yield cri.cmd.eq(0)
            for _ in range(5):yield
            self.assertEqual((yield d.count.status),6)
            yield d.enable.storage.eq(0)
            for _ in range(5):yield
            self.assertEqual((yield d.count.status),7)
            records=[]
            for i in (3,0,1,2):
                yield d.read_index.storage.eq(i)
                for _ in range(3):yield
                yield d.read_update.re.eq(1);yield
                yield d.read_update.re.eq(0);yield
                raw=(yield d.data.status).to_bytes(32,'big')
                records.append(decode_message(raw))
            self.assertEqual([r.timestamp for r in records[:3]],[103,104,105])
            self.assertEqual([r.data for r in records[:3]],[13,14,15])
            self.assertTrue(all(isinstance(r,OutputMessage) for r in records[:3]))
            self.assertIsInstance(records[-1],StoppedMessage)
            yield d.clear.re.eq(1);yield
            yield d.clear.re.eq(0);yield
            self.assertEqual((yield d.count.status),0)
            yield d.enable.storage.eq(1);yield
            yield cri.cmd.eq(commands['write']);yield
            yield cri.cmd.eq(0)
            for _ in range(5):yield
            self.assertEqual((yield d.count.status),1)
        run_simulation(d,run())
