#!/usr/bin/env python3
"""Apply minimal Genesys diagnostics changes to generated AMD 2025.2 copies."""
import argparse
from pathlib import Path


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Unexpected AMD template: ' + old)
    return text.replace(old, new, 1)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--app', required=True, type=Path)
    p.add_argument('--bsp', required=True, type=Path)
    o = p.parse_args()
    source = o.app / 'src/main.c'
    text = source.read_text()
    text = replace_once(text, '{ 0x00, 0x0a, 0x35, 0x00, 0x01, 0x02 }',
                        '{ 0x02, 0x38, 0x3b, 0x7f, 0x02, 0x0d }')
    text = replace_once(text, 'init_platform();', 'init_platform();\n\txil_printf("GENESYS-ZU GEM0 DIAGNOSTIC AMD 2025.2, not ARTIQ\\r\\n");')
    start = text.index('\t\t\txil_printf("Configuring default IP')
    end = text.index('\n\t\t}', start)
    text = text[:start] + '\t\t\txil_printf("TEST ethernet_dhcp FAIL; no static fallback\\r\\n");\n\t\t\treturn 1;' + text[end:]
    text = replace_once(text, '\tdhcp_start(echo_netif);',
                        '\terr_t dhcp_result = dhcp_start(echo_netif);\n\tif (dhcp_result != ERR_OK) {\n\t\txil_printf("TEST ethernet_dhcp FAIL start=%d\\r\\n", dhcp_result);\n\t\treturn 1;\n\t}')
    text = replace_once(text, '\tprint_ip_settings(&ipaddr, &netmask, &gw);',
                        '\txil_printf("TEST ethernet_dhcp PASS\\r\\n");\n\tprint_ip_settings(&ipaddr, &netmask, &gw);')
    source.write_text(text)
    echo = o.app / 'src/echo.c'
    echo.write_text(replace_once(echo.read_text(), 'port 6001 will be echoed', 'port 7 will be echoed'))
    phy = o.bsp / 'libsrc/lwip220/src/lwip-2.2.0/contrib/ports/xilinx/netif/xemacpsif_physpeed.c'
    text = phy.read_text()
    start = text.index('static u32_t get_TI_phy_speed(XEmacPs *xemacpsp, u32_t phy_addr)\n{')
    end = text.index('static u32_t get_TI_phy_speed_sgmii', start)
    function = text[start:end]
    function = replace_once(function, 'timeout_counter == 5', 'timeout_counter == 20')
    function = replace_once(function, 'xil_printf("Start PHY autonegotiation \\r\\n");',
                            'xil_printf("Start PHY autonegotiation addr=%d \\r\\n", phy_addr);')
    phy.write_text(text[:start] + function + text[end:])


if __name__ == '__main__':
    main()
