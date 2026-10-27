"""C/Python framing interoperability and interruption controls. LGPL-3.0-or-later."""
import subprocess
import tempfile
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'diagnostics/ddr'))
from pit_terminal_receipt import accept


class Tests(unittest.TestCase):
    def test_optimized_sanitized_and_python_decoder(self):
        base = ROOT/'diagnostics/ddr/pit_collect'
        with tempfile.TemporaryDirectory() as directory:
            for flags in (['-O2'], ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer']):
                exe = Path(directory)/'terminal'
                subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', *flags,
                                '-I'+str(base), str(base/'pit_terminal_record.c'),
                                str(ROOT/'tests/fixtures/pit_terminal_record_host.c'), '-o', str(exe)], check=True)
                data = subprocess.check_output([str(exe)], timeout=5)
                result = accept(data, data, 0x123456789abcdef0, '12'*32)
                self.assertEqual(result['status'], 'IRQ_UNPROVEN')
                self.assertFalse(result['sleep_proven'])
                self.assertFalse(result['hardware_executed'])


if __name__ == '__main__':
    unittest.main()
