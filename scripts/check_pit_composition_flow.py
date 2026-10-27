"""Scoped static composition audit, never HW admission. LGPL-3.0-or-later."""
from collections import Counter
import re
import struct
from package_local_candidate import loads
from check_pit_word_stores import check as check_stores

ENTRY='pit_status_composition_audit'
FORWARDERS=('observe','disable','read_word','write_word','barrier')


def check(data, symbols_text, disassembly):
    machine, entry, segments=loads(data)
    if machine!=189 or entry!=0xffdc0050:raise ValueError('full PMU audit ELF required')
    symbols={}
    for line in symbols_text.splitlines():
        m=re.fullmatch(r'([0-9a-f]+) ([0-9a-f]+) [tT] (\S+)',line)
        if m:
            if m[3] in symbols:raise ValueError('duplicate function symbol')
            symbols[m[3]]=(int(m[1],16),int(m[2],16))
    required={ENTRY,'pit_terminal_audit','memset',*FORWARDERS}
    if not required<=set(symbols):raise ValueError('missing composition symbols')
    rows={}
    for line in disassembly.splitlines():
        m=re.fullmatch(r'\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)',line)
        if m:rows[int(m[1],16)]=(int(m[2],16),m[3].split()[0])
    def body(name):
        start,size=symbols[name]
        if not size or size%4:raise ValueError('bad function size')
        result=[]
        for pc in range(start,start+size,4):
            matches=[s for s in segments if s['address']<=pc and pc+4<=s['address']+s['filesz']]
            if len(matches)!=1 or pc not in rows:raise ValueError('missing unique instruction payload')
            s=matches[0];word=struct.unpack_from('<I',s['payload'],pc-s['address'])[0]
            if rows[pc][0]!=word:raise ValueError('stale disassembly')
            result.append((pc,word,rows[pc][1]))
        return result
    terminal=body('pit_terminal_audit')
    if [w for _,w,_ in terminal]!=[0xb8220004,0xba020004,0xb800fffc]:raise ValueError('wrong terminal loop')
    def target(pc,word):
        offset=word&65535;previous=rows.get(pc-4,(0,''))[0]
        if previous>>16==0xb000:
            offset|=(previous&65535)<<16
            return pc+(offset-(1<<32) if offset&(1<<31) else offset)
        return pc+(offset-65536 if offset&32768 else offset)
    ordinary={'addik','addk','and','andi','bsll','bslli','cmpu','imm','lw','lwi','or','pcmpeq','pcmpne','sw','swi','xor','xori'}
    branches={'beqi','beqid','bnei','bneid','bltid','bri','brid'}
    reports={}
    for name in (ENTRY,*FORWARDERS):
        store_report=check_stores(data,symbols_text,name)
        instructions=body(name);start,size=symbols[name];calls=[];indirect=[];returns=0;branch_count=0
        for index,(pc,word,op) in enumerate(instructions):
            if op in ordinary:
                if word>>24 in (0x98,0x99,0xb6,0xb8,0xb9,0xba,0xbc,0xbe):raise ValueError('hidden control opcode')
                continue
            if op=='brlid':
                if word>>16!=0xb9f4:raise ValueError('bad direct call encoding')
                calls.append(target(pc,word))
            elif op=='brald':
                if word&0xffff07ff!=0x99fc0000:raise ValueError('bad indirect call encoding')
                indirect.append((word>>11)&31)
            elif op in branches:
                if word>>24 not in (0xbc,0xbe,0xb8):raise ValueError('bad branch encoding')
                t=target(pc,word)
                if not start<=t<start+size or t%4:raise ValueError('branch escapes function')
                branch_count+=1
            elif op=='rtsd':
                if name==ENTRY or word!=0xb60f0008:raise ValueError('unexpected return')
                returns+=1
            else:raise ValueError('unreviewed instruction '+op)
            if op.endswith('d') and (index+1>=len(instructions) or instructions[index+1][2] not in ordinary):
                raise ValueError('unreviewed delay slot')
        if name==ENTRY:
            expected={'observe':3,'disable':1,'read_word':1,'write_word':3,'barrier':2,'memset':1,'pit_terminal_audit':1}
            if Counter(calls)!=Counter({symbols[n][0]:count for n,count in expected.items()}):raise ValueError('wrong direct callback/terminal targets')
            if Counter(indirect)!=Counter({25:3,26:2}) or returns:raise ValueError('wrong receipt callback inventory')
            if instructions[-2][2]!='brid':raise ValueError('entry fallthrough not reviewed')
        elif calls or indirect!=[3] or returns!=1:
            raise ValueError('wrong forwarding callback/return inventory')
        reports[name]={'direct_calls':len(calls),'indirect_calls':len(indirect),'internal_branches':branch_count,'returns':returns,'word_store_sites':store_report['word_store_sites']}
    return {'status':'SCOPED_COMPOSITION_FLOW_PASS_NOT_HARDWARE','functions':reports,
            'hardware_executed':False,'deployable':False,'destructive_test_allowed':False,
            'limits':'Static inventory/ranges only; callback identity/dataflow, liveness, library/exception paths and physical visibility unqualified'}
