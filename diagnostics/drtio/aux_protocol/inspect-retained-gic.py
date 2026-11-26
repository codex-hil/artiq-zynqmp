#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Offline retained GIC source/ELF inventory; never reads MMIO or live registers."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path

def macro(text,name):
 match=re.search(r'^#define\s+'+re.escape(name)+r'[ \t]+(0x[0-9a-fA-F]+|[0-9]+)[Uu]?[ \t]*(?:(?:/\*|//).*)?$',text,re.M)
 assert match,('Missing literal macro',name);return int(match[1],0)

def decode(encoded):return (encoded&0xfff)+(0 if encoded&0x400000 else 16 if encoded&0x100000 else 32)

def inspect(root):
 bsp=root/'bsp';sources=bsp/'libsrc';bindings=[]
 def read(path):
  text=path.read_text();bindings.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()});return text
 params=read(bsp/'include/xparameters.h');wrap=read(bsp/'include/xinterrupt_wrap.h');timer=read(bsp/'include/xtimer_config.h');hw=read(bsp/'include/xscugic_hw.h')
 config=read(sources/'scugic/src/xscugic_g.c');gic=read(sources/'scugic/src/xscugic.c')
 assert macro(wrap,'XINTC_INTRID_MASK')==0xfff and macro(wrap,'XINTC_INTR_TYPE_MASK')==0x100000 and macro(wrap,'XINTC_IS_SGI_INTR_MASK')==0x400000
 assert 'XGet_IntrOffset' in wrap and '16 : 32' in wrap
 priority=macro(wrap,'XINTERRUPT_DEFAULT_PRIORITY');mask=macro(hw,'XSCUGIC_INTR_PRIO_MASK');assert priority==0xa0 and mask==0xf8
 assert macro(timer,'XTICKTIMER_BASEADDRESS')==macro(params,'XPAR_XTTCPS_0_BASEADDR')==0xff110000
 assert '"arm,gic-400"' in config and '0xf9010000' in config and '0xf9020000' in config
 cpu_init=gic[gic.index('static void CPUInitialize('):gic.index('static void CPUInitialize(')+2200]
 assert 'XSCUGIC_CPU_PRIOR_OFFSET, 0xF0U' in cpu_init
 assert 'XSCUGIC_BIN_PT_OFFSET' not in cpu_init and 'XSCUGIC_ALIAS_BIN_PT_OFFSET' not in cpu_init
 app=read(root/'app/src/platform.c');dma=read(sources/'lwip220/src/lwip-2.2.0/contrib/ports/xilinx/netif/xemacpsif_dma.c');ttc=read(sources/'xiltimer/src/core/ttcps/ttcps.c')
 assert 'XTimer_SetHandler(TimerCounterHandler, 0, XINTERRUPT_DEFAULT_PRIORITY)' in app
 assert 'XSetupInterruptSystem(&xemacpsif->emacps, &XEmacPs_IntrHandler' in dma
 assert 'XSetupInterruptSystem(TtcPsInstPtr, XTtcPs_InterruptHandler' in ttc
 elf=root/'app/build/lwip_echo_server.elf';text=subprocess.check_output(['/srv/codex-hil-data/artiq-zynqmp/toolchains/abi-verified/root/usr/bin/llvm-objdump-19','-d',str(elf)],text=True)
 def block(name):
  a=text.index('<'+name+'>:');b=text.index('\n\n',a);return text[a:b]
 assert 'mov\tw2, #-0x60' in block('init_timer') and 'and\tw2, w2, #0xff' in block('XTimer_SetHandler')
 assert 'mov\tw4, #0xa0' in block('init_dma')
 assert 'and\tw0, w0, #0xffffff7f' in block('XSetupInterruptSystem') and 'msr\tDAIF, x0' in block('XSetupInterruptSystem')
 rows=[];dist=0xf9010000;cpu=0xf9020000
 for role,name in [('tick','XPAR_XTTCPS_0_INTERRUPTS'),('GEM','XPAR_XEMACPS_0_INTERRUPTS')]:
  encoded=macro(params,name);irq=decode(encoded)
  rows.append({'role':role,'encoded_interrupt':hex(encoded),'irq_id':irq,'requested_priority':hex(priority),'masked_priority':hex(priority&mask),
   'source_register_locations':{'enable_word':hex(dist+macro(hw,'XSCUGIC_ENABLE_SET_OFFSET')+(irq//32)*4),'enable_bit':irq%32,'priority_word':hex(dist+macro(hw,'XSCUGIC_PRIORITY_OFFSET')+(irq//4)*4),'priority_byte_shift':(irq%4)*8}})
 assert [r['irq_id'] for r in rows]==[68,89]
 expected_offsets={'XSCUGIC_CONTROL_OFFSET':0,'XSCUGIC_CPU_PRIOR_OFFSET':4,'XSCUGIC_BIN_PT_OFFSET':8,'XSCUGIC_ALIAS_BIN_PT_OFFSET':0x1c,'XSCUGIC_RUN_PRIOR_OFFSET':0x14,'XSCUGIC_INT_ACK_OFFSET':0xc,'XSCUGIC_EOI_OFFSET':0x10}
 assert all(macro(hw,n)==v for n,v in expected_offsets.items()),'Register map changed; require review'
 registers={n:hex(cpu+macro(hw,n)) for n in ('XSCUGIC_CONTROL_OFFSET','XSCUGIC_CPU_PRIOR_OFFSET','XSCUGIC_BIN_PT_OFFSET','XSCUGIC_ALIAS_BIN_PT_OFFSET','XSCUGIC_RUN_PRIOR_OFFSET')}
 forbidden={hex(cpu+macro(hw,n)) for n in ('XSCUGIC_INT_ACK_OFFSET','XSCUGIC_EOI_OFFSET')};assert not forbidden&set(registers.values())
 return {'status':'RETAINED_GIC_SOURCE_AND_ELF_PRIORITY_INVENTORY_PASS_NOT_LIVE_STATE','interrupts':rows,'cpu_priority_mask_source':'0xf0 if retained initialization path executes','binary_point':'No BPR/ABPR write in retained CPUInitialize; inherited/active values unknown','recovery':'Retained XSetupInterruptSystem clears DAIF.I; source/equal requested priorities do not qualify actual IRQ nesting','future_snapshot_metadata_only':registers,'excluded_ack_eoi_addresses':sorted(forbidden),'not_executed':True,'required_unknowns':['Complete enabled interrupt set including inherited SGI/PPI/SPI/FIQ sources','Live PMR/BPR/ABPR/security-group/CPU-target banks and running priorities','Source-to-current-image identity, CPU0 currentEL/DAIF and snapshot consistency','Worst-case priority/preemption/nesting and FPU/exception stack model'],'source_bindings':bindings,'retained_elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),'hardware_accessed':False,'runtime_admitted':False,'limits':['Register addresses are source-derived metadata only, not a collector or authorization to access HW','Acknowledgement/EOI registers deliberately excluded; no reads/writes/reset/halt were performed','No conclusion that timer and GEM are the only enabled interrupts or that one IRQ layer is sufficient']},'\n\n'.join(block(n) for n in ('init_timer','XTimer_SetHandler','XTimer_TtcSetIntrHandler','init_dma','XSetupInterruptSystem'))

def main():
 p=argparse.ArgumentParser();p.add_argument('--retained',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r,text=inspect(a.retained);a.output.mkdir(parents=True,exist_ok=True);(a.output/'report.json').write_text(json.dumps(r,indent=2)+'\n');(a.output/'linked-priority-context.txt').write_text(text+'\n');print(r['status'])
if __name__=='__main__':main()
