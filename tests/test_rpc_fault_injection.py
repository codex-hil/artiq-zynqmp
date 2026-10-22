"""One-shot fault observation and restoration controls; LGPL-3.0-or-later."""
import socket,sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'common/artiq'));sys.path.insert(0,str(REPO/'scripts'))
from inject_rpc_fault import inject,Injected
from prepare_rpc_fault_plan import cases
from test_candidate_runtime_hw import lifecycle


class FaultInjection(unittest.TestCase):
    def comm(self):
        comm=Mock();comm._read_bool.return_value=False;comm._read_int32.return_value=42
        comm._receive_rpc_args.return_value=([0x1234567887654321,100,1.25],{})
        comm._read_bytes.return_value=b'f';comm.socket.recv.return_value=b''
        return comm

    def test_cases_send_exactly_once_and_half_close_only_partial(self):
        for case in cases():
            with self.subTest(case=case['name']):
                comm=self.comm();report={}
                with self.assertRaises(Injected):inject(comm,None,case,report)
                comm._write_chunk.assert_called_once_with(bytes.fromhex(case['body_hex']))
                comm._flush.assert_called_once();self.assertTrue(report['connection_terminated'])
                self.assertEqual(comm.socket.shutdown.call_count,int(case['half_close']))

    def test_unexpected_request_sends_nothing(self):
        comm=self.comm();comm._read_bytes.return_value=b'i'
        report={}
        with self.assertRaises(ValueError):inject(comm,None,cases()[0],report)
        self.assertEqual(report['observed_request']['return_tags_hex'],'69')
        comm._write_header.assert_not_called();comm._flush.assert_not_called()

    def test_timeout_or_wrong_data_cannot_pass_and_restores(self):
        for failure in ('timeout','unexpected_data'):
            comm=self.comm();report={};seen=[]
            if failure=='timeout':comm.socket.recv.side_effect=socket.timeout('bounded timeout')
            else:comm.socket.recv.return_value=b'x'
            def cycle(role):
                seen.append(role)
                if role=='candidate':inject(comm,None,cases()[0],report)
                return 'restored'
            result=lifecycle(cycle)
            self.assertEqual(result['status'],'FAIL');self.assertEqual(result['restoration'],'PASS')
            self.assertEqual(seen,['candidate','restore']);self.assertNotIn('connection_terminated',report)

if __name__=='__main__':unittest.main()
