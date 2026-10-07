#!/usr/bin/env python3
"""Physical trusted-kernel ABI diagnostic on A53 CPU1; no physical RTIO output."""
import argparse
import hashlib
import json
import socket
import struct
import subprocess
import time
from pathlib import Path
import serial


def validate_image(path, bits):
    data = path.read_bytes()
    elf_class = 1 if bits == 32 else 2
    if data[:6] != b'\x7fELF' + bytes([elf_class, 1]):
        raise ValueError(f'Wrong diagnostic ELF class/endianness: {path}')
    machine = struct.unpack_from('<H', data, 18)[0]
    if machine != (40 if bits == 32 else 183):
        raise ValueError('Wrong diagnostic ELF architecture')
    if bits == 32:
        entry, phoff = struct.unpack_from('<II', data, 24)
        phsize, phnum = struct.unpack_from('<HH', data, 42)
        base, limit = 0x20200000, 0x20400000
    else:
        entry, phoff = struct.unpack_from('<QQ', data, 24)
        phsize, phnum = struct.unpack_from('<HH', data, 54)
        base, limit = 0x20000000, 0x20010000
    if entry != base: raise ValueError('Unexpected diagnostic entry point')
    loads = 0
    for index in range(phnum):
        offset = phoff + index * phsize
        if bits == 32:
            kind, fileoff, va, pa, filesz, memsz, flags, align = struct.unpack_from('<IIIIIIII', data, offset)
        else:
            kind, flags, fileoff, va, pa, filesz, memsz, align = struct.unpack_from('<IIQQQQQQ', data, offset)
        if kind != 1: continue
        if not (base <= pa <= limit and pa + memsz <= limit and va == pa and filesz <= memsz and fileoff + filesz <= len(data)):
            raise ValueError('Diagnostic segment outside reserved memory')
        loads += 1
    if not loads: raise ValueError('No diagnostic load segments')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['server', 'cable', 'serial', 'positive', 'negative', 'ip', 'output']:
        p.add_argument('--' + name, required=True)
    o = p.parse_args()
    output = Path(o.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve().with_name('run_kernel_cpu1.tcl')
    result = {'kind': 'hardware', 'scope': 'A53 CPU1 loader and kernel ABI diagnostic; RTIO is a memory model, no physical experiment',
              'time': time.time(), 'cable': o.cable, 'tests': {}, 'artifacts_sha256': {}}

    def metadata():
        # Management framing already independently tested with upstream CommMgmt.
        with socket.create_connection((o.ip, 1380), timeout=5) as s:
            s.sendall(b'ARTIQ management\n\0')
            if s.recv(1) != b'e': raise RuntimeError('CPU0 handshake failed')
            key = b'board'
            s.sendall(b'\x0c' + struct.pack('<I', len(key)) + key)
            def exact(n):
                data = b''
                while len(data) < n:
                    part = s.recv(n - len(data))
                    if not part: raise RuntimeError('CPU0 management closed')
                    data += part
                return data
            if exact(1) != b'\x07': raise RuntimeError('CPU0 metadata reply failed')
            value = exact(struct.unpack('<I', exact(4))[0])
            if value != b'genesys_zu-5ev': raise RuntimeError('Wrong board')
            return value.decode()

    try:
        result['management_before'] = metadata()
        for name, directory, expected in [('positive', o.positive, 'PASS'), ('negative', o.negative, 'FAIL')]:
            directory = Path(directory).resolve()
            images = [directory / 'probe32.elf', directory / 'start64.elf']
            for image, bits in zip(images, [32, 64]):
                validate_image(image, bits)
                result['artifacts_sha256'][str(image)] = hashlib.sha256(image.read_bytes()).hexdigest()
            with serial.Serial(o.serial, 115200, timeout=.2) as uart:
                uart.reset_input_buffer()
                proc = subprocess.run(['vivado-container', 'shell', '-c',
                    'exec /srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb "$@"',
                    'xsdb', str(script), o.server, *map(str, images), o.cable, expected],
                    capture_output=True, text=True, timeout=60)
                text = uart.read(4096).decode('ascii', errors='replace')
            (output / (name + '-jtag.log')).write_text(proc.stdout + proc.stderr)
            (output / (name + '-uart.log')).write_text(text)
            marker = 'PASS: A53 bare-metal NAC3 kernel' if name == 'positive' else 'FAIL: bare-metal kernel ABI probe'
            if proc.returncode or 'PASS: AArch32 CPU1 reads real PL RTIO counter' not in text or marker not in text or (name == 'negative' and 'PASS: A53 bare-metal NAC3 kernel' in text):
                raise RuntimeError(f'{name} diagnostic failed; see JTAG/UART logs')
            result['tests'][name] = 'PASS'  # negative PASS means wrong ABI was rejected
            result['management_after_' + name] = metadata()
        result['tests']['cpu0_management_continues'] = 'PASS'
        result['tests']['aarch32_cpu1_ps_pl_counter'] = 'PASS'
        result['tests']['ttl_physical'] = 'NOT_RUN'
        result['status'] = 'PASS'
    except Exception as e:
        result['status'] = 'FAIL'
        result['failure'] = str(e)
    (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
