"""Actual C collector failure/publication tests. LGPL-3.0-or-later."""
import subprocess
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


class Tests(unittest.TestCase):
    def test_optimized_and_sanitized(self):
        base = ROOT / 'diagnostics/ddr/pit_collect'
        with tempfile.TemporaryDirectory() as directory:
            for flags in (['-O2'], ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer']):
                exe = Path(directory) / 'collector'
                subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', *flags,
                                '-I' + str(base), str(base / 'pit_collect.c'),
                                str(ROOT / 'tests/fixtures/pit_collect_host.c'), '-o', str(exe)], check=True)
                subprocess.run([str(exe)], check=True, timeout=5)


if __name__ == '__main__':
    unittest.main()
