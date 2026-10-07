#!/usr/bin/env python3
"""Actual ARTIQ network upload/run/RPC on Genesys; no TTL output."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import socket
import struct
import subprocess
import sys
import time
from artiq.coredevice.comm_kernel import CommKernel, LoadError, Reply, Request
from artiq.coredevice.comm_mgmt import CommMgmt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ip', required=True)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--runs', type=int, default=5)
    o = p.parse_args()
    if o.runs < 1: p.error('--runs must be positive')
    repo = Path(__file__).resolve().parent.parent
    out = o.output.resolve();out.mkdir(parents=True, exist_ok=True)
    db = out / 'device_db.py'
    db.write_text((repo / 'examples/device_db_genesys.py').read_text().replace('192.168.2.16',o.ip))
    socket.setdefaulttimeout(10)
    result = {'kind':'hardware','time':time.time(),'ip':o.ip,
        'scope':'actual network ARM32 kernel load/run and scalar RPC; no physical TTL output', 'tests':{},'runs':[]}
    client = None

    def management(check_busy=False):
        with_mgmt = CommMgmt(o.ip)
        try:
            with_mgmt.open()
            mode=with_mgmt.config_read('runtime_mode')
            board=with_mgmt.config_read('board')
            if mode!=b'kernel-bringup' or board!=b'genesys_zu-5ev': raise RuntimeError('Unexpected board/runtime mode')
            if check_busy:
                try: with_mgmt.config_read('rtio_counter')
                except OSError as e:
                    if 'Device failed to read config' not in str(e): raise
                else: raise RuntimeError('CPU0 counter latch accessed while CPU1 runs')
                result['tests']['shared_counter_latch_guard']='PASS'
            else:
                if int(with_mgmt.config_read('rtio_counter'))<=0: raise RuntimeError('Idle counter access failed')
        finally: with_mgmt.close()

    try:
        management();result['tests']['management_before']='PASS'
        for name, source in [('network', 'genesys_network_probe.py'), ('ttl', 'genesys_ttl.py')]:
            proc=subprocess.run([str(Path(sys.executable).with_name('artiq_compile')), '--device-db',str(db),
                '--dataset-db',str(out/'datasets.mdb'),'-o',str(out/(name+'.elf')),'-d',str(out/(name+'-debug.elf')),
                str(repo/'examples'/source)],capture_output=True,text=True,timeout=30)
            (out/(name+'-compile.log')).write_text(proc.stdout+proc.stderr)
            if proc.returncode: raise RuntimeError('Compilation failed: '+name)
        elf=(out/'network.elf').read_bytes()
        result['network_elf_sha256']=hashlib.sha256(elf).hexdigest()
        client=CommKernel(o.ip);client.check_system_info()
        for name,bad in [('invalid',b'not an ELF'),('out_of_bounds',elf[:28]+b'\xfc\xff\xff\xff'+elf[32:]),('unsupported_ttl',(out/'ttl.elf').read_bytes())]:
            try: client.load(bad)
            except LoadError as e:
                if name=='unsupported_ttl' and 'rtio_output' not in str(e): raise
                result['tests'][name+'_rejected']='PASS'
                result.setdefault('load_errors',{})[name]=str(e)
            else: raise RuntimeError('Invalid/unsupported kernel falsely loaded: '+name)
        # Bound violation rejected from its length header, without sending giant data.
        client._write_header(Request.LoadKernel);client._write_int32(1024*1024+1);client._flush()
        client._read_header();client._read_expect(Reply.LoadFailed)
        result['oversize_error']=client._read_string()
        result['tests']['oversized_upload_rejected']='PASS'
        client.close();client=None
        client=CommKernel(o.ip);client.check_system_info()
        client._write_header(Request.LoadKernel);client._write_int32(len(elf));client._flush()
        for offset in range(0,len(elf),31):client.socket.sendall(elf[offset:offset+31])
        client._read_empty(Reply.LoadCompleted)
        result['tests']['fragmented_real_elf_load']='PASS'
        second=CommKernel(o.ip)
        try:
            try: second.open()
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):result['tests']['exclusive_kernel_owner']='PASS'
            else:raise RuntimeError('Second kernel owner accepted')
        finally:second.close()
        management();result['tests']['management_during_kernel_ownership']='PASS'
        client.close();client=None
        for index in range(o.runs):
            env=dict(os.environ, PYTHONUNBUFFERED='1', GENESYS_TEST_RPC_DELAY='1' if index==0 else '0')
            proc=subprocess.Popen([str(Path(sys.executable).with_name('artiq_run')),'--device-db',str(db),
                '--dataset-db',str(out/'datasets.mdb'),str(repo/'examples/genesys_network_probe.py')],
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=env)
            lines=[];sel=selectors.DefaultSelector();sel.register(proc.stdout,selectors.EVENT_READ)
            try:
                deadline=time.monotonic()+40
                while time.monotonic()<deadline:
                    for key,_ in sel.select(.2):
                        line=key.fileobj.readline()
                        if line:
                            lines.append(line)
                            if index==0 and line.startswith('NETWORK_KERNEL_RPC '):
                                management(check_busy=True);result['tests']['management_while_cpu1_waits_rpc']='PASS'
                    if proc.poll() is not None:
                        lines.append(proc.stdout.read());break
                else:
                    proc.kill();proc.wait();raise RuntimeError('artiq_run timed out')
            finally:
                sel.close()
                if proc.poll() is None:
                    proc.terminate();proc.wait(timeout=3)
            text=''.join(lines);(out/f'run-{index}.log').write_text(text)
            if proc.returncode or 'NETWORK_KERNEL_RPC 0x1234567887654321 ' not in text or 'NETWORK_KERNEL_RETURN_PASS 3.75' not in text:
                raise RuntimeError(f'Real artiq_run/RPC failed: run {index}')
            result['runs'].append({'index':index,'returncode':proc.returncode,'stdout':text})
        result['tests']['real_artiq_run_repeated_load_execute']='PASS'
        result['tests']['i64_counter_float_rpc_and_sync_return']='PASS'
        management();result['tests']['management_after']='PASS'
        mgmt=CommMgmt(o.ip)
        try:
            mgmt.open()
            result['runtime_log']=mgmt.get_log()
        finally:mgmt.close()
        if 'CPU1 kernel finished.' not in result['runtime_log']:raise RuntimeError('No actual kernel completion log')
        result['tests']['ttl_physical']='NOT_RUN'
        result['status']='PASS'
    except Exception as e:
        result['status']='FAIL';result['failure']=str(e)
    finally:
        if client is not None:client.close()
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
