"""Storage admission and pre-hardware ordering controls; LGPL-3.0-or-later."""
import contextlib,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
REPO=Path(__file__).resolve().parents[1];sys.path.insert(0,str(REPO/'scripts'))
import check_hw_storage as storage
import test_candidate_runtime_hw as candidate
import load_rtio_runtime as loader

class Storage(unittest.TestCase):
    def stats(self,bytes=storage.MIN_BYTES,inodes=storage.MIN_INODES):
        return SimpleNamespace(f_bavail=bytes,f_frsize=1,f_favail=inodes)
    def test_boundary_and_symlink_missing_output_ancestor(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'link').symlink_to(root,target_is_directory=True)
            with patch.object(storage.os,'statvfs',return_value=self.stats()) as probe:
                report=storage.inspect(dict(new=root/'link/new/deep'))
                self.assertEqual(report['status'],'STORAGE_ADMISSION_PASS')
                self.assertEqual(report['entries'][0]['probe_path'],str(root));probe.assert_called_once()
    def test_low_bytes_inodes_or_one_low_role_refused(self):
        for values in ([self.stats(bytes=storage.MIN_BYTES-1)],[self.stats(inodes=storage.MIN_INODES-1)],[self.stats(),self.stats(bytes=0)]):
            with patch.object(storage.os,'statvfs',side_effect=values):
                report=storage.inspect({str(n):Path('/tmp') for n in range(len(values))})
                self.assertEqual(report['status'],'STORAGE_ADMISSION_FAIL')
    def test_candidate_refuses_before_lease_subprocess_or_output_creation(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'new';manifest=Path(d)/'manifest';manifest.write_text('{}')
            argv=['candidate','--manifest',str(manifest),'--output',str(out),'--execute','--server','fixture','--port','fixture','--interface','fixture']
            with patch.object(sys,'argv',argv),patch.object(candidate,'preflight',return_value={}),patch.object(candidate,'require_runtime_space',side_effect=RuntimeError('Storage refused')),patch.object(candidate,'lease') as lease,patch.object(candidate,'bounded') as run:
                with self.assertRaisesRegex(RuntimeError,'Storage refused'):candidate.main()
                lease.assert_not_called();run.assert_not_called();self.assertFalse(out.exists())
    def test_recheck_under_lease_still_prevents_hardware(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'new';manifest=Path(d)/'manifest';manifest.write_text('{}')
            argv=['candidate','--manifest',str(manifest),'--output',str(out),'--execute','--server','fixture','--port','fixture','--interface','fixture']
            with patch.object(sys,'argv',argv),patch.object(candidate,'preflight',return_value={}),patch.object(candidate,'require_runtime_space',side_effect=[{'status':'PASS'},RuntimeError('Space changed')]),patch.object(candidate,'lease',return_value=contextlib.nullcontext(object())),patch.object(candidate,'bounded') as run:
                with self.assertRaisesRegex(RuntimeError,'Space changed'):candidate.main()
                run.assert_not_called()

    def test_direct_loader_refuses_before_uart(self):
        with tempfile.TemporaryDirectory() as d:
            argv=['load']
            for name in ('server','cable','port','ps-export','bitstream','worker','cpu0'):argv+=['--'+name,'fixture']
            argv+=['--output',str(Path(d)/'new')]
            with patch.object(sys,'argv',argv),patch.object(loader,'require_runtime_space',side_effect=RuntimeError('Storage refused')),patch.object(loader.serial,'Serial') as uart,patch.object(loader.subprocess,'run') as run:
                with self.assertRaisesRegex(RuntimeError,'Storage refused'):loader.main()
                uart.assert_not_called();run.assert_not_called()

if __name__=='__main__':unittest.main()
