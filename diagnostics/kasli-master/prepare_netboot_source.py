"""Create a separate checked ARTIQ laboratory netboot worktree.

LGPL-3.0-or-later. Preserves source checkout and all board persistent storage.
"""
import argparse
import json
from pathlib import Path
import subprocess

REVISION = '486e8f897547d282d46a02c30463449c21e30cfe'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    revision = subprocess.check_output(['git', '-C', str(args.source), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != REVISION:
        raise SystemExit('Source revision changed; review overlay before use')
    if args.output.exists():
        raise SystemExit('Output already exists; refusing to overwrite a worktree')
    subprocess.run(['git', '-C', str(args.source), 'worktree', 'add', '--detach', str(args.output), REVISION], check=True)
    boot = args.output / 'artiq/firmware/bootloader/main.rs'
    text = boot.read_text()
    guard = 'if !config::read_str("no_flash_boot", |r| r == Ok("1")) {'
    if text.count(guard) != 1:
        raise SystemExit('Flash boot guard changed; review required')
    boot.write_text(text.replace(guard, '// KASLI03 laboratory image: network/RAM boot only.\n        if false {'))
    net = args.output / 'artiq/firmware/libboard_misoc/net_settings.rs'
    text = net.read_text()
    start = text.index('    let hardware_addr;\n', text.index('pub fn get_addresses()'))
    end = text.index('    let ipv6_ll_addr =', start)
    text = text[:start] + '''    // Unique volatile laboratory identity; do not read/write board storage.
    let hardware_addr = EthernetAddress([0x02, 0x4b, 0x03, 0x48, 0x48, 0x54]);
    let ipv4_addr = Ipv4AddrConfig::UseDhcp;
    let ipv4_default_route = None;

''' + text[end:]
    start = text.index('    let ipv6_addr = match config::read_str("ip6"')
    end = text.index('\n    };', start) + len('\n    };')
    text = text[:start] + '    let ipv6_addr = None;' + text[end:]
    start = text.index('    let ipv6_default_route = match config::read_str("ip6_default_route"')
    end = text.index('\n    };', start) + len('\n    };')
    text = text[:start] + '    let ipv6_default_route = None;' + text[end:]
    net.write_text(text)
    patch = subprocess.check_output(['git', '-C', str(args.output), 'diff'], text=True)
    (args.output / 'kasli03-netboot.patch').write_text(patch)
    (args.output / 'kasli03-netboot.json').write_text(json.dumps({
        'upstream_revision': revision, 'boot': 'network/RAM only',
        'mac': '02:4b:03:48:48:54', 'ipv4': 'DHCP',
        'scope': 'KASLI03 laboratory; no persistent writes',
        'clock_profile': 'upstream volatile Si5324 initialization retained'
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
