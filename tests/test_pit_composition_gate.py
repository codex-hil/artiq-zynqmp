"""Exact closure, refusal and CLI controls. LGPL-3.0-or-later."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pit_composition_audit_gate as gate
from pmu_guard_candidate import preflight as old_hardware_gate


class Tests(unittest.TestCase):
    def setup_manifest(self,root):
        for name in gate.SOURCES|gate.SCRIPTS:
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'synthetic source')
        artifacts={}
        for name in ('elf','symbols','disassembly'):
            path=root/name;path.write_bytes(b'synthetic artifact')
            artifacts[name]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        return {'schema':1,'profile':gate.PROFILE,'deployable':False,'hardware_executed':False,
                'source_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in gate.SOURCES},
                'script_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in gate.SCRIPTS},'artifacts':artifacts}

    def test_each_changed_pin_rejected_before_structural_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);manifest=self.setup_manifest(root)
            paths=[root/n for n in gate.SOURCES|gate.SCRIPTS]+[Path(v['path']) for v in manifest['artifacts'].values()]
            self.assertEqual(len(paths),26)
            for path in paths:
                old=path.read_bytes();path.write_bytes(old+b'changed')
                with patch.object(gate,'check_layout') as layout,patch.object(gate,'check_flow') as flow:
                    with self.assertRaises(ValueError):gate.audit(manifest,root)
                    layout.assert_not_called();flow.assert_not_called()
                path.write_bytes(old)

    def test_shape_flags_and_deployment_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);manifest=self.setup_manifest(root)
            for field,value in [('schema',True),('profile','sleep'),('deployable',True),('hardware_executed',True),('execute',True)]:
                bad=copy.deepcopy(manifest);bad[field]=value
                with self.assertRaises(ValueError):gate.audit(bad,root)
            for field in ('source_sha256','script_sha256','artifacts'):
                bad=copy.deepcopy(manifest);bad[field].pop(next(iter(bad[field])))
                with self.assertRaises(ValueError):gate.audit(bad,root)
            with self.assertRaisesRegex(ValueError,'never deployable'):gate.require_deployment(manifest,execute=True)
            path=root/'manifest.json';path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):old_hardware_gate(path,ROOT)
            result=subprocess.run([sys.executable,str(ROOT/'scripts/pit_composition_audit_gate.py'),
                                   '--manifest',str(path),'--execute'],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertIn('unrecognized arguments: --execute',result.stderr)


if __name__=='__main__':unittest.main()
