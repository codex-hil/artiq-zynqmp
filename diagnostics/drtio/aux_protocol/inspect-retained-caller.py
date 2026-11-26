#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Bind standalone frame probes to retained CPU0 object code, never deploy."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path

def sections(path):
    b=path.read_bytes();assert b[:6]==b'\x7fELF\x02\x01'
    off=struct.unpack_from('<Q',b,40)[0];size,count,names=struct.unpack_from('<HHH',b,58)
    headers=[struct.unpack_from('<IIQQQQIIQQ',b,off+i*size) for i in range(count)]
    h=headers[names];strings=b[h[4]:h[4]+h[5]]
    return {strings[h[0]:strings.index(b'\0',h[0])].decode():b[h[4]:h[4]+h[5]] for h in headers if h[1]!=8}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--retained',type=Path,required=True);p.add_argument('--probe',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    sources=a.retained/'app/src';objects=a.retained/'app/build/CMakeFiles/lwip_echo_server.elf.dir';elf=a.retained/'app/build/lwip_echo_server.elf'
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    bindings=[];frames={}
    commands=json.loads((sources/'compile_commands.json').read_text())
    assert any(Path(r['file']).name=='platform.c' for r in commands)
    assert not any(Path(r['file']).name=='platform_zynqmp.c' for r in commands)
    for name in ('main.c','platform.c','kernel_lwip.c'):
        old=objects/(name+'.obj');new=a.probe/(name+'.o');left,right=sections(old),sections(new)
        assert left['.text']==right['.text'],('Code changed',name)
        assert left.get('.rela.text')==right.get('.rela.text'),('Relocations changed',name)
        assert sha(sources/name)==sha(a.probe/'input/app/src'/name)
        for line in (a.probe/(name+'.su')).read_text().splitlines():
            origin,size,qualifier=line.split('\t');assert qualifier=='static';frames[origin.rsplit(':',1)[-1]]=int(size)
        bindings.append({'source':str(sources/name),'source_sha256':sha(sources/name),'retained_object_sha256':sha(old),'probe_object_sha256':sha(new),'text_and_relocations_identical':True,'text_sha256':hashlib.sha256(left['.text']).hexdigest()})
    assert frames['main']==80 and frames['timer_callback']==16 and frames['TimerCounterHandler']==32
    maintext=(sources/'main.c').read_text();loop=maintext[maintext.index('while (1) {'):]
    ordered=['tcp_fasttmr();','tcp_slowtmr();','xemacif_input(echo_netif);','transfer_data();','genesys_kernel_poll();']
    positions=[loop.index(x) for x in ordered];assert positions==sorted(positions)
    platform=(sources/'platform.c').read_text();assert 'XTimer_SetHandler(TimerCounterHandler' in platform
    dis=subprocess.check_output(['/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/bin/llvm-objdump-19','-d','--disassemble-symbols=main,IRQInterruptHandler,IRQInterrupt,XScuGic_InterruptHandler,timer_callback,TimerCounterHandler',str(elf)],text=True)
    assert '<XScuGic_InterruptHandler>:' in dis and '<IRQInterrupt>:' in dis
    assert 'br\tx16' in dis and 'blr\tx1' in dis
    a.output.mkdir(parents=True,exist_ok=True);(a.output/'linked-disassembly.txt').write_text(dis)
    r={'status':'RETAINED_CPU0_CALLER_AND_TIMER_FRAME_PROBE_CODE_IDENTITY_PASS','runtime_admitted':False,'hardware_accessed':False,'retained_elf_sha256':sha(elf),'object_bindings':bindings,'app_frames_bytes':frames,
       'foreground_order':ordered,'candidate_boundary':'After genesys_kernel_poll returns, before next loop iteration, only under separately qualified worker/link ownership grant; no hook inserted',
       'actual_interrupt_path':'IRQInterruptHandler -> IRQInterrupt exception-table tail dispatch -> XScuGic_InterruptHandler -> dynamic registered handler; timer uses SDT XTimer handler -> TimerCounterHandler -> timer_callback',
       'irq_open_items':['Resolve all enabled GIC handler registrations, including GEM and timer wrapper, rather than only timer','Timer path can call DHCP timers and eth_link_detect; transitive C/library stack remains unknown','Assembly fixed save208B is lower bound; IRQ nesting/masking, FPU trap context, other exceptions and live EL/SP remain unqualified'],
       'limits':['Retained October artifact, not current device state','80B main plus isolated576B diagnostic sum is not a production bound: different link/callbacks and IRQ omitted','genesys_kernel_poll busy/event fields alone are not a worker quiescence/ownership handshake','No runtime modification, board access or admission'],
       'next':'Inventory actual retained GIC registrations and timer/GEM transitive callees with frame metadata and nesting policy; keep candidate foreground hook disabled.'}
    (a.output/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
if __name__=='__main__':main()
