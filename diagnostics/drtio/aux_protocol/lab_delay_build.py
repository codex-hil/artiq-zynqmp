"""Strict laboratory delay map and generated source overlay; LGPL-3.0-or-later."""

def validate_map(mapping):
    dma=mapping.get('dma') or {};cfg=dma.get('laboratory_read_delay') or {}
    if (cfg.get('sys_clk_hz')!=125000000 or cfg.get('delay_us')!=2000 or cfg.get('cycles')!=250000 or
        cfg.get('ps_clock_source',{}).get('configured_hz')!=125000000):
        raise ValueError('Lab firmware requires checked Genesys 125MHz/2ms map')
    names=['arm','armed','holding','arm_rejected','triggers','rejected','cycles']
    for i,name in enumerate(names):
        key='dma_lab_delay_'+name
        expected=dict(address=0xa0002048+4*i,words=1,bits=1 if i<3 else 32)
        if dma.get('registers',{}).get(key)!=expected or mapping.get('registers',{}).get(key)!=expected:
            raise ValueError('Unexpected laboratory delay register: '+key)
    return cfg['cycles']


def source_overlay(original):
    include='#include "ddma_runtime.h"'
    poll='  ddma_poll();'
    if 'ddma_lab_runtime.h' in original or original.count(include)!=1 or original.count(poll)!=1:
        raise ValueError('Unrecognized firmware injection anchors')
    return original.replace(include,include+'\n#include "ddma_lab_runtime.h"').replace(poll,poll+'''
  if(XUartPs_IsReceiveData(STDIN_BASEADDRESS)) {
   unsigned command=XUartPs_ReadReg(STDIN_BASEADDRESS,XUARTPS_FIFO_OFFSET)&255;
   if(command=='F')ddma_lab_request();
  }''')
