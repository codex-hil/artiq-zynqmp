#!/usr/bin/env python3
"""OCM UART environment observation under inherited lease; LGPL-3.0-or-later."""
import argparse,json,subprocess,time
from pathlib import Path
from inject_rpc_fault import require_lease
from check_ocm_image import check
from decode_ocm_environment import decode


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('server','port','elf','symbols','ps-init','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();require_lease()
    import serial
    out=Path(a.output)
    if out.exists():raise ValueError('Use fresh observation directory')
    layout=check(Path(a.elf).read_bytes(),Path(a.symbols).read_text());out.mkdir(parents=True)
    lines=[];result=dict(status='FAIL',hardware_executed=True,ddr_test='NOT_RUN')
    repo=Path(__file__).resolve().parents[1]
    try:
        with serial.Serial(a.port,115200,timeout=.2,write_timeout=1) as uart:
            uart.reset_input_buffer()
            cmd=['vivado-container','shell','-c','exec "$@"','bash','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/xsdb',str(repo/'scripts/run_ocm_environment.tcl'),a.server,a.elf,a.ps_init,'210383B7F02DA']
            try:r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
            except subprocess.TimeoutExpired as error:
                (out/'load.log').write_text(str(error.output or '')+str(error.stderr or ''));raise
            (out/'load.log').write_text(r.stdout+r.stderr)
            if r.returncode:raise RuntimeError('OCM loader failed')
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                text=uart.readline().decode('ascii',errors='replace').strip()
                if not text:continue
                lines.append(text)
                if text=='UART ECHO READY':uart.write(b'PING');uart.flush()
                if text.startswith('BRINGUP COMPLETE'):break
            else:raise RuntimeError('OCM UART completion timeout')
        text='\n'.join(lines)+'\n'
        if 'TEST ddr NOT_RUN OCM-only diagnostic' not in text or 'TEST ddr PASS' in text:raise RuntimeError('Expected OCM-only DDR exclusion')
        result.update(status='PASS',environment=decode(text,layout))
    except Exception as error:result['error']=str(error)
    finally:
        (out/'uart.log').write_text('\n'.join(lines)+'\n')
        (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
