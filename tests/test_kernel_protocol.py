"""Wire-level regression tests; these do not claim hardware execution."""
import io
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
    "common/petalinux/meta-petalinux-artiq/recipes-artiq/artiq-cored/artiq-cored"))
from artiq_cored.comm.kernel import CommKernel


class Stream:
    def __init__(self, payload):
        self.rx = io.BytesIO(payload)
        self.tx = io.BytesIO()

    def read(self, size):
        return self.rx.read(size)

    def write(self, data):
        return self.tx.write(data)

    def flush(self):
        pass


class KernelProtocol(unittest.TestCase):
    def exchange(self, request, payload=b""):
        stream = Stream(b"ARTIQ coredev\n" + b"\x5a" * 4 + bytes([request]) + payload)
        CommKernel("kernel", 1381)._handle_stream(stream)
        return stream.tx.getvalue()

    def test_load_fails_explicitly(self):
        reply = self.exchange(5, struct.pack("<I", 4) + b"ELF!")
        self.assertEqual(reply[:6], b"e" + b"\x5a" * 4 + b"\x06")
        size, = struct.unpack("<I", reply[6:10])
        self.assertEqual(reply[10:], b"Kernel execution backend is not implemented")
        self.assertEqual(size, len(reply[10:]))

    def test_run_never_reports_execution(self):
        self.assertEqual(self.exchange(6), b"e" + b"\x5a" * 4 + b"\x08")

    def test_truncated_length(self):
        self.assertEqual(self.exchange(5, b"\x01"), b"e")

    def test_truncated_elf(self):
        self.assertEqual(self.exchange(5, struct.pack("<I", 8) + b"ELF!"), b"e")

    def test_oversized_elf(self):
        reply = self.exchange(5, struct.pack("<I", CommKernel.MAX_KERNEL_SIZE + 1))
        self.assertEqual(reply[5], 6)

    def test_reject_invalid_hello(self):
        stream = Stream(b"wrong hello!!!")
        CommKernel("kernel", 1381)._handle_stream(stream)
        self.assertEqual(stream.tx.getvalue(), b"")


if __name__ == "__main__":
    unittest.main()
