from logging import getLogger
from socket import socket
from io import BufferedRWPair
from struct import pack, unpack

from ..server import Server

_LOGGER = getLogger(__name__)


class CommKernel(Server):
    DEFAULT_NAME = "kernel"
    DEFAULT_PORT = 1381

    COREDEV_HELLO = b"ARTIQ coredev\n"
    COREDEV_REPLY = b"e"
    SYNC_CHAR = b"\x5A"
    SYNC_LEN = 4
    MAX_KERNEL_SIZE = 16 * 1024 * 1024

    def _handle_client(self, c_sock: socket) -> None:
        with c_sock.makefile("brw") as c_io:
            self._handle_stream(c_io)

    def _handle_stream(self, c_io: BufferedRWPair) -> None:

        hello = c_io.read(len(self.COREDEV_HELLO))
        _LOGGER.debug("hello = %r", hello)
        if hello != self.COREDEV_HELLO:
            _LOGGER.warning("Incorrect hello")
            return
        c_io.write(self.COREDEV_REPLY)
        c_io.flush()

        while True:
            req = self._sync(c_io)
            if len(req) == 0:
                return
            _LOGGER.debug("req = 0x%02X", *req)

            req_handler = {
                0x03: self._req_system_info,
                0x05: self._req_load_kernel,
                0x06: self._req_run_kernel,
            }.get(*req)
            if req_handler is None:
                _LOGGER.warning("Invalid request")
                return

            if req_handler(c_io) is False:
                return

    def _sync(self, c_io: BufferedRWPair) -> bytes:
        sync = 0
        while True:
            by = c_io.read(1)
            if len(by) == 0:
                return by
            elif by == self.SYNC_CHAR:
                sync += 1
            elif sync < self.SYNC_LEN:
                _LOGGER.warning("No SYNC")
                return b""
            else:
                return by

    def _req_system_info(self, c_io: BufferedRWPair) -> None:
        ident = b"bringup-not-a-core-device;Genesys-ZU"
        c_io.write(self.SYNC_LEN * self.SYNC_CHAR)
        c_io.write(b"\x02")
        c_io.write(b"AROR")
        c_io.write(pack("<I", len(ident)))
        c_io.write(ident)
        c_io.write(b"\x00")
        c_io.flush()

    def _req_load_kernel(self, c_io: BufferedRWPair) -> bool:
        length = c_io.read(4)
        if len(length) != 4:
            return False
        elf_len, = unpack("<I", length)
        if elf_len > self.MAX_KERNEL_SIZE:
            self._load_failed(c_io, b"Kernel exceeds bring-up server size limit")
            return False
        if len(c_io.read(elf_len)) != elf_len:
            return False
        self._load_failed(c_io, b"Kernel execution backend is not implemented")
        return True

    def _load_failed(self, c_io: BufferedRWPair, reason: bytes) -> None:
        c_io.write(self.SYNC_LEN * self.SYNC_CHAR)
        c_io.write(b"\x06")  # ARTIQ Reply.LoadFailed
        c_io.write(pack("<I", len(reason)))
        c_io.write(reason)
        c_io.flush()

    def _req_run_kernel(self, c_io: BufferedRWPair) -> None:
        c_io.write(self.SYNC_LEN * self.SYNC_CHAR)
        c_io.write(b"\x08")  # ARTIQ Reply.KernelStartupFailed
        c_io.flush()
