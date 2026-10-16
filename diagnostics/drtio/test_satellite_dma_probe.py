"""Decode the exact host DDR image using native ARTIQ; LGPL-3.0-or-later."""
import unittest,subprocess,tempfile
from pathlib import Path
from migen import passive
from migen.sim import run_simulation
from artiq.gateware.rtio.dma import RecordSlicer
from satellite_dma_probe import trace_bytes,make_tcl,abort_trace_bytes,qualified_dma_shape,make_abort_tcl

class ProbeTests(unittest.TestCase):
    def abort_mapping(self):
        names="""monitor_magic aux_in_reset aux_rtio_reset_request aux_phy_reset_request
        aux_rt_reply_fault aux_rtio_error_flags aux_rx_up aux_tsc_load_count
        dma_active dma_clear dma_accepted dma_completed dma_address dma_time_offset
        dma_max_bursts dma_watchdog dma_start dma_pending dma_reject dma_result_error
        dma_result_channel dma_result_timestamp dma_abort aux_tsc_snapshot_request
        aux_tsc_snapshot_busy aux_tsc_snapshot_valid aux_tsc_snapshot_value
        aux_rtio_reset_applied aux_phy_reset_applied""".split()
        return dict(dma={'arena':{'base':0x22000000,'size':0x200000,'alignment':128}},
                    registers={n:dict(address=0xa0000000+8*i,words=2 if n in
                      ('dma_time_offset','aux_tsc_snapshot_value','dma_result_timestamp') else 1)
                      for i,n in enumerate(names)})

    def test_abort_plan_executes_in_mock_tcl_and_rejects_faults(self):
        # Execute generated control flow, but replace MMIO/DDR by Tcl mocks.
        # No XSDB connection, lease or hardware involved.
        mock=r"""
rename rd mmio_rd
rename wr mmio_wr
array set state {monitor_magic 1146246192 aux_rx_up 1 aux_tsc_load_count 1 aux_tsc_snapshot_valid 1 aux_tsc_snapshot_value 1000}
proc rd {name} {global state;if {[info exists state($name)]} {return $state($name)};return 0}
proc wr {name value} {
 global state early abort_error
 set state($name) $value
 if {$name eq "aux_tsc_snapshot_request"} {incr state(aux_tsc_snapshot_value) 1000}
 if {$name eq "dma_start"} {
  set state(dma_accepted) 1;set state(dma_active) 1
  if {$early} {set state(dma_pending) 1;set state(dma_completed) 1;set state(dma_active) 0}
 }
 if {$name eq "dma_abort"} {
  set state(dma_active) 0;set state(dma_pending) 1;set state(dma_completed) 1;set state(dma_result_error) $abort_error
 }
}
proc mwr {args} {global memory;set memory [binary_read [lindex $args 2]]}
proc mrd {args} {
 global memory corrupt
 set f [open [lindex $args 2] wb]
 if {$corrupt} {puts -nonewline $f "bad"} else {puts -nonewline $f $memory}
 close $f
}
proc disconnect {} {}
"""
        mapping=self.abort_mapping()
        for early,error,corrupt,offset,expected in (
            (0,1,0,30000000000,'SATELLITE_DMA_ABORT_DRAIN_PASS'),
            (1,1,0,30000000000,'DMA did not remain active'),
            (0,33,0,30000000000,'Unexpected abort result'),
            (0,1,1,30000000000,'DDR block readback mismatch'),
            (0,1,0,8000,'Insufficient future offset')):
            with self.subTest(early=early,error=error,corrupt=corrupt,offset=offset),tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);(directory/'trace.bin').write_bytes(abort_trace_bytes())
                script=make_abort_tcl(mapping,offset)
                marker='if {[rd monitor_magic]'
                script=script.replace(marker,f'set early {early};set abort_error {error};set corrupt {corrupt}\n'+mock+'\n'+marker,1)
                path=directory/'probe.tcl';path.write_text(script)
                result=subprocess.run(['tclsh',str(path)],capture_output=True,text=True,timeout=5)
                self.assertIn(expected,result.stdout+result.stderr)
                self.assertEqual(result.returncode==0,early==0 and error==1 and corrupt==0 and offset==30000000000)

    def test_abort_wrapper_requires_exact_idle_proof_and_host_only_mode(self):
        from types import SimpleNamespace
        from host_dma_session import validate
        import json
        with tempfile.TemporaryDirectory() as tmp:
            proof=Path(tmp)/'idle.json'
            data=dict(status='PASS',restoration='PASS',external_rx=dict(
                dio_loopback='PASS',restoration='PASS',bit_sha256='bit',firmware_sha256='firmware'))
            proof.write_text(json.dumps(data))
            c=dict(host_dma_abort_test=True,abort_acknowledgement='host-only-32768-byte-window',
                   dma_idle_qualification=str(proof))
            session=SimpleNamespace(config=c,native_ddma=False,snapshot_test=True,
                dio_test=True,mapping={'dma':True},result={'bit_sha256':'bit','firmware_sha256':'firmware'})
            validate(session)
            for field,value in [('native_ddma',True),('snapshot_test',False)]:
                original=getattr(session,field);setattr(session,field,value)
                with self.assertRaises(ValueError):validate(session)
                setattr(session,field,original)
            c['abort_acknowledgement']=''
            with self.assertRaises(ValueError):validate(session)
            c['abort_acknowledgement']='host-only-32768-byte-window'
            session.result['firmware_sha256']='different'
            with self.assertRaises(ValueError):validate(session)

    def test_abort_fixture_exceeds_sed_capacity_and_is_bounded(self):
        data=abort_trace_bytes()
        self.assertEqual(len(data),256*128)
        self.assertGreater(1100,8*128)
        for i in range(1100):
            record=data[i*17:(i+1)*17]
            self.assertEqual(record[:4],bytes([17,0,0,0]))
            self.assertEqual(int.from_bytes(record[4:12],'little'),1000000+i*16000)
            self.assertEqual(record[12],0)
            self.assertEqual(int.from_bytes(record[13:17],'little'),1-i%2)
        self.assertFalse(any(data[1100*17:]))

    def test_known_routed_cdc_shapes_only(self):
        for groups,endpoints in ((6,164),(8,170)):
            q=dict(status='PASS',groups=groups,endpoints=endpoints,
                   requirement_ns=8,minimum_slack_ns=0)
            self.assertTrue(qualified_dma_shape(q))
            for key,value in [('status','FAIL'),('groups',7),('endpoints',169),
                              ('requirement_ns',9),('minimum_slack_ns',-0.01)]:
                self.assertFalse(qualified_dma_shape(dict(q,**{key:value})))

    def decode(self,data):
        d=RecordSlicer(64);records=[];terminated=[]
        @passive
        def monitor():
            while True:
                if (yield d.source.stb) and (yield d.source.ack):
                    records.append(((yield d.source.channel),(yield d.source.timestamp),
                                    (yield d.source.address),(yield d.source.data)))
                if (yield d.end_marker_found):terminated.append(1)
                yield
        def run():
            yield d.source.ack.eq(1)
            # DMAReader reverses little-endian DDR words before RecordSlicer.
            for offset in range(0,len(data),8):
                yield d.sink.data.eq(int.from_bytes(data[offset:offset+8],'big'))
                yield d.sink.stb.eq(1);yield
                for _ in range(100):
                    if (yield d.sink.ack) or terminated:break
                    yield
                else:self.fail('Native decoder stalled')
                yield d.sink.stb.eq(0);yield
                if terminated:break
            for _ in range(30):yield
        run_simulation(d,[run(),monitor()])
        self.assertTrue(terminated)
        return records

    def test_abort_fixture_native_decoder(self):
        records=self.decode(abort_trace_bytes())
        self.assertEqual(records,[(0,1000000+i*16000,0,1-i%2) for i in range(1100)])

    def test_exact_ddr_bytes_decode_with_native_record_slicer(self):
        data=trace_bytes();records=self.decode(data)
        expected=[(1,0,2,3)]
        for i in range(4):
            t=1000000+i*80000
            expected.extend([(0,t,0,1),(0,t+8000,0,0)])
        expected.append((1,2000000,2,0))
        self.assertEqual(records,expected)
        self.assertEqual(len(data),2048)
        self.assertFalse(any(data[171:]))

    def test_invalid_epoch_or_arena_rejected_before_hardware(self):
        for ts in (0,-8,9,2**63):
            with self.assertRaises(ValueError):make_tcl({},ts)
        with self.assertRaisesRegex(ValueError,'arena'):make_tcl({},8000)

if __name__=='__main__':unittest.main()
