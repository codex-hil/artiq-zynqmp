#!/usr/bin/env python3
"""Attach Piotr-style Rust staticlib services to a generated AMD/lwIP app."""
import argparse
import json
from pathlib import Path
import shutil


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--app', required=True, type=Path)
    p.add_argument('--staticlib', required=True, type=Path)
    p.add_argument('--csr-map', required=True, type=Path)
    p.add_argument('--kernel', action='store_true')
    o = p.parse_args()
    repo = Path(__file__).resolve().parent.parent
    mapping = json.loads(o.csr_map.read_text())
    if mapping['csr_base'] != 0xA0000000 or mapping['csr_data_width'] != 32:
        raise ValueError('Unsupported CSR ABI')
    source = o.app / 'src'
    shutil.copyfile(repo / 'boards/genesys_zu-5ev/2_firmware_a53/c/management_lwip.c', source / 'management_lwip.c')
    regs = mapping['registers']
    if regs['rtio_counter']['words'] != 2 or regs['rtio_counter_update']['words'] != 1:
        raise ValueError('Unexpected RTIO counter ABI')
    (source / 'rtio_csr.h').write_text(f"#define RTIO_COUNTER 0x{regs['rtio_counter']['address']:X}UL\n#define RTIO_COUNTER_UPDATE 0x{regs['rtio_counter_update']['address']:X}UL\n")
    main = source / 'main.c'
    text = main.read_text()
    text = text.replace('#include "platform.h"', '#include "platform.h"\n#include <stdio.h>\nextern int genesys_management_start(const unsigned char *, size_t);')
    old = '\tprint_ip_settings(&ipaddr, &netmask, &gw);'
    if text.count(old) != 1:
        raise ValueError('Unexpected AMD application')
    text = text.replace(old, old + '''
    char ip_text[16];
    int ip_len = snprintf(ip_text, sizeof(ip_text), "%u.%u.%u.%u", ip4_addr1(&ipaddr), ip4_addr2(&ipaddr), ip4_addr3(&ipaddr), ip4_addr4(&ipaddr));
    if (ip_len <= 0 || ip_len >= (int)sizeof(ip_text) || genesys_management_start((const unsigned char *)ip_text, (size_t)ip_len)) {
        xil_printf("Management service initialization failed\\r\\n");
        return 1;
    }
''')
    if o.kernel:
        shutil.copyfile(repo / 'boards/genesys_zu-5ev/2_firmware_a53/c/kernel_lwip.c', source / 'kernel_lwip.c')
        text = text.replace('extern int genesys_management_start(const unsigned char *, size_t);',
            'extern int genesys_management_start(const unsigned char *, size_t);\nextern int genesys_kernel_start(void);\nextern void genesys_kernel_poll(void);')
        anchor = '\t/* start the application (web server, rxtest, txtest, etc..) */'
        if text.count(anchor) != 1: raise ValueError('Unexpected AMD startup anchor')
        text = text.replace(anchor, '    if (genesys_kernel_start()) { xil_printf("Kernel worker unavailable\\r\\n"); return 1; }\n' + anchor)
        if text.count('\t\ttransfer_data();') != 1: raise ValueError('Unexpected AMD poll loop')
        text = text.replace('\t\ttransfer_data();', '\t\ttransfer_data();\n        genesys_kernel_poll();')
    main.write_text(text)
    cmake = source / 'CMakeLists.txt'
    text = cmake.read_text().replace('collect (PROJECT_LIB_SOURCES echo.c)', 'collect (PROJECT_LIB_SOURCES echo.c)\ncollect (PROJECT_LIB_SOURCES management_lwip.c)')
    if o.kernel:
        text = text.replace('collect (PROJECT_LIB_SOURCES management_lwip.c)', 'collect (PROJECT_LIB_SOURCES management_lwip.c)\ncollect (PROJECT_LIB_SOURCES kernel_lwip.c)')
    text += '\ntarget_link_libraries(${APP_NAME}.elf "' + str(o.staticlib.resolve()) + '")\n'
    cmake.write_text(text)


if __name__ == '__main__':
    main()
