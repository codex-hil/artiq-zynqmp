"""Regression: separate IP outputs and relocate copied XCI metadata only."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from diag_gateware import DiagnosticPlatform


class ImportTests(unittest.TestCase):
    def test_two_ips_have_independent_outputs_and_preserve_sources(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = []
            original = {}
            for name in ('ps', 'gth'):
                source = root / 'original' / (name + '.xci')
                source.parent.mkdir(exist_ok=True)
                data = {'ip_inst': {'gen_directory': '../../../old.gen/' + name,
                    'parameters': {'component_parameters': {'profile': name},
                        'runtime_parameters': {'OUTPUTDIR': [{'value': '../../../old.gen/' + name}]}}}}
                source.write_text(json.dumps(data))
                original[source] = source.read_bytes()
                sources.append(str(source))
            class Platform:
                ips = sources
            copied = DiagnosticPlatform.copy_ips(Platform(), root/'build')
            self.assertEqual(copied, {'ip/ps/ps.xci', 'ip/gth/gth.xci'})
            for source in original:
                self.assertEqual(source.read_bytes(), original[source])
                inst = json.loads((root/'build'/'ip'/source.stem/source.name).read_text())['ip_inst']
                self.assertEqual(inst['gen_directory'], './')
                self.assertEqual(inst['parameters']['runtime_parameters']['OUTPUTDIR'][0]['value'], './')
                self.assertEqual(inst['parameters']['component_parameters']['profile'], source.stem)
