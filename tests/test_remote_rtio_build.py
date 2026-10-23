"""Remote result negative controls, no hardware; LGPL-3.0-or-later."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_remote_rtio_build import check

class RemoteBuildTests(unittest.TestCase):
    def fixture(self,root):
        files={'exit.json':json.dumps(dict(returncode=0)),'top.bit':'new-bitstream',
            'top.v':'pinned HDL','console.log':'Build completed',
            'top_timing.rpt':'WNS(ns) TNS(ns)\n-------\n1.2 0 0 20 0.1 0 0 20 2.5 0 0 10\nAll user specified timing constraints are met.\nchecking no_clock (0)\nchecking unconstrained_internal_endpoints (0)\nchecking no_input_delay (1)\nchecking no_output_delay (5)',
            'top_drc.rpt':'REPORT SUMMARY\nChecks found: 1\n| RTSTAT-10 | Warning | No routable loads | 1 |',
            'top_route_status.rpt':'# of routable nets..... : 10 :\n# of fully routed nets..... : 10 :\n# of nets with routing errors.......... : 0 :'}
        for k,v in files.items():(root/k).write_text(v)
        return dict(files=[dict(path='top.v',build_sha256=hashlib.sha256(b'pinned HDL').hexdigest())])

    def test_no_master_requires_exact_netlist_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);m=self.fixture(root);m['profile']='no-ddr-master'
            with self.assertRaises(FileNotFoundError):check(root,m)
            proof=root/'no_ddr_master_nets.rpt'
            good='SAXIGP2ARVALID GROUND\nSAXIGP2AWVALID GROUND\nSAXIGP2WVALID GROUND\nNO_DDR_MASTER_NETLIST_PASS\n'
            proof.write_text(good);self.assertIn('no_ddr_master_netlist_sha256',check(root,m))
            proof.write_text(good.replace('GROUND','POWER',1))
            with self.assertRaises(ValueError):check(root,m)

    def test_valid_reports_retain_io_limitations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);m=self.fixture(root);r=check(root,m)
            self.assertEqual(r['status'],'FPGA_BUILD_PASS_NOT_HARDWARE')
            self.assertEqual(r['timing_coverage']['no_output_delay'],5)
            self.assertEqual(r['drc_warnings'],['RTSTAT-10'])

    def test_bad_exit_input_timing_drc_route_and_log_rejected(self):
        bad={'exit.json':'{"returncode":1}','top.v':'changed',
            'top_timing.rpt':'Timing failed',
            'top_drc.rpt':'REPORT SUMMARY\n| NSTD-1 | Error | unspecified IO | 1 |',
            'top_route_status.rpt':'# of nets with routing errors..... : 1 :',
            'console.log':'CRITICAL WARNING: implementation issue'}
        for name,value in bad.items():
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);m=self.fixture(root);(root/name).write_text(value)
                with self.assertRaises(ValueError):check(root,m)

    def test_numeric_failure_coverage_and_incomplete_routing_rejected(self):
        for name,old,new in [('top_timing.rpt','1.2 0 0 20','-0.2 0 0 20'),
                             ('top_timing.rpt','unconstrained_internal_endpoints (0)','unconstrained_internal_endpoints (1)'),
                             ('top_route_status.rpt','fully routed nets..... : 10','fully routed nets..... : 9'),
                             ('top_drc.rpt','Checks found: 1','Checks found: 2')]:
            with self.subTest(name=name,old=old),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);m=self.fixture(root);path=root/name
                path.write_text(path.read_text().replace(old,new))
                with self.assertRaises(ValueError):check(root,m)

    def test_missing_bitstream_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);m=self.fixture(root);(root/'top.bit').unlink()
            with self.assertRaises(ValueError):check(root,m)

if __name__=='__main__':unittest.main()
