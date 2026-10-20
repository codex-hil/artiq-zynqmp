"""Synthetic UART idle states only; LGPL-3.0-or-later."""
import unittest
from lab_idle_probe import FIELDS,parse,probe

def sample(**kwargs):
    values={name:0 for name in FIELDS};values.update(ready=1,epoch=7,edges=16);values.update(kwargs)
    return 'AUX_DDMA LAB_IDLE '+' '.join(n+'='+str(values[n]) for n in FIELDS)+'\n'
class UART:
    timeout=.01;in_waiting=0
    def __init__(self):self.writes=[];self.pending=b''
    def write(self,data):self.writes.append(data);self.pending=sample().encode();return len(data)
    def read(self,n):data=self.pending;self.pending=b'';return data
class IdleTests(unittest.TestCase):
    def test_read_only_two_samples(self):
        uart=UART();self.assertEqual(probe(uart,bytearray(),settle=.02)['lab_idle_counters'],'PASS')
        self.assertEqual(uart.writes,[b'I',b'I'])
    def test_negative_states_and_epoch(self):
        for name in FIELDS:
            if name in ('ready','epoch','edges'):continue
            with self.assertRaises(ValueError):parse(sample()+sample(**{name:1}))
        for text in [sample(),sample()*3,sample()+sample(epoch=8),sample()+sample(edges=17),
                     sample(ready=0)*2,sample(epoch=0)*2,sample(ar=1,rlast=1)*2]:
            with self.assertRaises(ValueError):parse(text)
