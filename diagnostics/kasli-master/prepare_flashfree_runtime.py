"""Prepare isolated RAM-only Kasli runtime source. LGPL-3.0-or-later."""
import argparse
from pathlib import Path
import subprocess


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise SystemExit('Upstream shape changed; review runtime overlay')
    return text.replace(old, new)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite a source worktree')
    repo = Path(__file__).resolve().parents[2]
    subprocess.run(['git', '-C', str(args.source), 'worktree', 'add', '--detach', str(args.output),
                    '486e8f897547d282d46a02c30463449c21e30cfe'], check=True)
    subprocess.run(['git', '-C', str(args.output), 'apply',
                    str(repo / 'diagnostics/kasli-master/kasli03-netboot.patch')], check=True)
    build = args.output / 'artiq/build_soc.py'
    text = replace_once(build.read_text(),
                        '        builder.software_packages = [p for p in builder.software_packages if p[0] == "bootloader"]\n', '')
    text = replace_once(text, '"bootloader_only": True,', '"bootloader_only": False,')
    build.write_text(text)
    main_rs = args.output / 'artiq/firmware/runtime/main.rs'
    text = replace_once(main_rs.read_text(),
        'use board_misoc::{csr, ident, clock, spiflash, config, net_settings, pmp, boot};',
        'use board_misoc::{csr, ident, clock, config, net_settings, pmp, boot};\n'
        '#[cfg(has_spiflash)]\nuse board_misoc::spiflash;')
    text = replace_once(text, '            spiflash::reload();',
                        '            #[cfg(has_spiflash)]\n            spiflash::reload();\n'
                        '            #[cfg(not(has_spiflash))]\n            loop {}')
    main_rs.write_text(text)
    mgmt = args.output / 'artiq/firmware/runtime/mgmt.rs'
    original = mgmt.read_text()
    boundary = original.index('#[cfg(has_drtio)]\nmod remote_coremgmt')
    text = replace_once(original[:boundary], '    use board_misoc::{config, mem, spiflash};',
                        '    use board_misoc::config;\n    #[cfg(has_spiflash)]\n'
                        '    use board_misoc::{mem, spiflash};')
    for name in ('reboot', 'flash'):
        text = replace_once(text, '    pub fn ' + name + '(',
                            '    #[cfg(has_spiflash)]\n    pub fn ' + name + '(')
    needle = '    pub fn debug_allocator('
    replacement = '''    // Flash/reconfiguration are unavailable in the RAM-only laboratory image.
    #[cfg(not(has_spiflash))]
    pub fn reboot(_io: &Io, stream: &mut TcpStream) -> Result<(), Error<SchedError>> {
        Reply::Error.write_to(stream)?;
        Ok(())
    }
    #[cfg(not(has_spiflash))]
    pub fn flash(_io: &Io, stream: &mut TcpStream, _image: &[u8]) -> Result<(), Error<SchedError>> {
        Reply::Error.write_to(stream)?;
        Ok(())
    }

    pub fn debug_allocator('''
    text = replace_once(text, needle, replacement)
    mgmt.write_text(text + original[boundary:])
    patch = subprocess.check_output(['git', '-C', str(args.output), 'diff'], text=True)
    (args.output / 'kasli03-flashfree-runtime.patch').write_text(patch)


if __name__ == '__main__':
    main()
