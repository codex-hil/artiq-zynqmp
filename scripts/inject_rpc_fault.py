#!/usr/bin/env python3
"""One RPC fault under inherited Genesys lease; LGPL-3.0-or-later.

Only called inside test_candidate_runtime_hw.py's restoration window.
"""
import argparse,fcntl,json,os,runpy,socket,sys
from pathlib import Path
from prepare_rpc_fault_plan import cases


class Injected(BaseException):pass


def require_lease():
    path=Path.home()/'.cache/genesys-210383B7F02DA.lock'
    fd=int(os.environ['GENESYS_LEASE_FD']);a=os.fstat(fd);b=path.stat()
    if (a.st_dev,a.st_ino)!=(b.st_dev,b.st_ino):raise ValueError('Wrong inherited Genesys lease')
    # Conflicts with a different owner's file description; never replace the lease.
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    return fd


def inject(comm,embedding,case,report):
    from artiq.coredevice.comm_kernel import Request
    asynchronous=comm._read_bool();service=comm._read_int32()
    args,kwargs=comm._receive_rpc_args(embedding);tags=comm._read_bytes()
    if asynchronous or not service or kwargs or tags!=b'f' or len(args)!=3 or args[0]!=0x1234567887654321 or args[1]<=0 or args[2]!=1.25:
        raise ValueError('Unexpected RPC request; no injection performed')
    report.update(request_verified=True,return_tags=tags.decode(),service_id=service)
    comm.socket.settimeout(5)
    comm._write_header(Request.RPCReply);comm._write_chunk(bytes.fromhex(case['body_hex']));comm._flush()
    report['injection_sent']=True
    if case['half_close']:comm.socket.shutdown(socket.SHUT_WR)
    try:reply=comm.socket.recv(1)
    except ConnectionResetError:reply=b''
    if reply:raise RuntimeError('Unexpected data instead of connection termination')
    report['connection_terminated']=True
    raise Injected()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=[c['name'] for c in cases()],required=True)
    parser.add_argument('--ip',required=True);parser.add_argument('--device-db',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);a=parser.parse_args()
    require_lease()
    if a.output.exists():raise ValueError('Use a fresh fault output')
    a.output.mkdir(parents=True)
    from artiq.coredevice.comm_kernel import CommKernel
    from artiq.coredevice.comm_mgmt import CommMgmt
    selected=next(c for c in cases() if c['name']==a.case)
    report=dict(status='FAIL',hardware_executed=True,case=selected,worker_cancellation_progress='NOT_PROVEN',reuse_after_fault=False)
    original=CommKernel._serve_rpc;injected=False
    def hook(comm,embedding):
        nonlocal injected
        if injected:raise RuntimeError('Only one injection allowed')
        injected=True;inject(comm,embedding,selected,report)
    CommKernel._serve_rpc=hook
    saved=sys.argv[:]
    try:
        sys.argv=['artiq_run','--device-db',str(a.device_db),'--dataset-db',str(a.output/'datasets.mdb'),str(Path(__file__).resolve().parents[1]/'examples/genesys_network_probe.py')]
        try:runpy.run_module('artiq.frontend.artiq_run',run_name='__main__')
        except Injected:pass
        if not report.get('connection_terminated'):raise RuntimeError('Fault observation not completed')
        m=CommMgmt(a.ip)
        try:
            m.open();m.socket.settimeout(5)
            if m.config_read('board')!=b'genesys_zu-5ev':raise RuntimeError('Wrong management identity')
            report['management_log']=m.get_log();report['management_alive']=True
        finally:m.close()
        report['status']='FAULT_TERMINATION_OBSERVED_RESTORE_REQUIRED'
    except Exception as error:report['error']=str(error)
    finally:
        sys.argv=saved;CommKernel._serve_rpc=original
        (a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='FAULT_TERMINATION_OBSERVED_RESTORE_REQUIRED' else 1

if __name__=='__main__':raise SystemExit(main())
