"""One-shot fault observation and restoration controls; LGPL-3.0-or-later."""
import importlib.util,io,socket,struct,sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
from inject_rpc_fault import inject,Injected
from prepare_rpc_fault_plan import cases
from test_candidate_runtime_hw import lifecycle


class FaultInjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('rpc_fixture',REPO/'examples/genesys_network_probe.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        cls.probe=module.GenesysNetworkProbe

    def embedding(self):
        embedding=Mock();embedding.retrieve_function.return_value=self.probe.report
        return embedding

    def comm(self):
        comm=Mock();comm._read_bool.return_value=False;comm._read_int32.return_value=42
        comm._receive_rpc_args.return_value=([object.__new__(self.probe),0x1234567887654321,100,1.25],{})
        comm._read_bytes.return_value=b'f';comm.socket.recv.return_value=b''
        return comm

    def test_cases_send_exactly_once_and_half_close_only_partial(self):
        for case in cases():
            with self.subTest(case=case['name']):
                comm=self.comm();report={}
                with self.assertRaises(Injected):inject(comm,self.embedding(),case,report)
                comm._write_chunk.assert_called_once_with(bytes.fromhex(case['body_hex']))
                comm._flush.assert_called_once();self.assertTrue(report['connection_terminated'])
                self.assertEqual(comm.socket.shutdown.call_count,int(case['half_close']))

    def test_actual_nac3_host_decodes_receiver_as_first_argument(self):
        from artiq.coredevice.comm_kernel import CommKernel
        receiver=object.__new__(self.probe);embedding=self.embedding()
        embedding.retrieve_object.return_value=receiver
        wire=(b'\0'+struct.pack('<i',173)+b'O'+struct.pack('<i',1)
            +b'I'+struct.pack('<q',0x1234567887654321)+b'I'+struct.pack('<q',100)
            +b'f'+struct.pack('<d',1.25)+b'\0'+struct.pack('<i',1)+b'f')
        comm=CommKernel('unused');comm.endian='<'
        comm.unpack_int32=struct.Struct('<i').unpack;comm.unpack_int64=struct.Struct('<q').unpack
        comm.unpack_float64=struct.Struct('<d').unpack;comm._read=io.BytesIO(wire).read
        comm.socket=Mock();comm.socket.recv.return_value=b''
        comm._write_header=Mock();comm._write_chunk=Mock();comm._flush=Mock()
        report={}
        with self.assertRaises(Injected):inject(comm,embedding,cases()[0],report)
        self.assertEqual(report['observed_request']['argument_count'],4)
        embedding.retrieve_object.assert_called_once_with(1)

    def test_unexpected_request_sends_nothing(self):
        comm=self.comm();comm._read_bytes.return_value=b'i'
        report={}
        with self.assertRaises(ValueError):inject(comm,self.embedding(),cases()[0],report)
        self.assertEqual(report['observed_request']['return_tags_hex'],'69')
        comm._write_header.assert_not_called();comm._flush.assert_not_called()

    def test_timeout_or_wrong_data_cannot_pass_and_restores(self):
        for failure in ('timeout','unexpected_data'):
            comm=self.comm();report={};seen=[]
            if failure=='timeout':comm.socket.recv.side_effect=socket.timeout('bounded timeout')
            else:comm.socket.recv.return_value=b'x'
            def cycle(role):
                seen.append(role)
                if role=='candidate':inject(comm,self.embedding(),cases()[0],report)
                return 'restored'
            result=lifecycle(cycle)
            self.assertEqual(result['status'],'FAIL');self.assertEqual(result['restoration'],'PASS')
            self.assertEqual(seen,['candidate','restore']);self.assertNotIn('connection_terminated',report)

if __name__=='__main__':unittest.main()
