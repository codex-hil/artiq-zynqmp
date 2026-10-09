"""Strict UART client for the temporary XIicPs register service."""
import time
import serial

class Client:
    def __init__(self, port, log):
        self.serial = serial.Serial(port, 115200, timeout=.2)
        self.log = log
    def close(self):
        self.serial.close()
    def command(self, command, prefix):
        self.serial.write((command+'\n').encode())
        deadline = time.monotonic()+5
        while time.monotonic() < deadline:
            raw = self.serial.readline()
            if not raw:
                continue
            self.log.write(raw.decode(errors='replace')); self.log.flush()
            line = raw.decode(errors='replace').strip()
            if line.startswith(('ERR ', 'SI_CONTROL_FAIL')):
                raise RuntimeError(line)
            if line.startswith(prefix):
                return line.split()
        raise TimeoutError(command)
    def read(self, address):
        response = self.command(f'R{address:04X}', 'READ ')
        if int(response[1],16) != address:
            raise RuntimeError(response)
        return int(response[2],16)
    def write(self, address, value):
        response = self.command(f'W{address:04X}{value:02X}', 'WRITE ')
        if int(response[1],16) != address or int(response[2],16) != value or int(response[3]):
            raise RuntimeError(response)
    def checked_write(self, address, value):
        self.write(address, value)
        if self.read(address) != value:
            raise RuntimeError(f'Write verification failed: {address:04x}')
