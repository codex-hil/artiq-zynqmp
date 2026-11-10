#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact LUT truth tables to sequential Q cutpoints; not sequential/CDC proof."""
import itertools,json,re,sys
from pathlib import Path
def norm(s):return re.sub(r'xilinxmultiregimpl([0-4])_xilinxmultiregimpl([0-4][01])',r'xilinxmultiregimpl\2',s)
class Network:
 def __init__(self,path):
  self.cells={};self.pins={};self.drivers={}
  for line in path.read_text().splitlines():
   f=line.split('\t')
   if f[0]=='CELL':self.cells[f[1]]=(f[2],f[3])
   elif f[0]=='PIN':
    self.pins[f[1]]=f[3]
    if f[2]=='OUT' and f[3]:self.driver(f[3],f[1])
   elif f[0]=='PORT' and f[2]=='IN' and f[3]:self.driver(f[3],'PORT/'+f[1])
 def driver(self,net,pin):
  if net in self.drivers:raise ValueError('Multiple drivers')
  self.drivers[net]=pin
 def expression(self,pin):
  visiting=set()
  def net_expr(net):
   if net in visiting:raise ValueError('Combinational loop')
   visiting.add(net);driver=self.drivers[net]
   if driver.startswith('PORT/'):result=('var',driver)
   else:
    cell,port=driver.rsplit('/',1);ref,init=self.cells[cell]
    if ref in ('FDRE','FDPE'):
     if port!='Q':raise ValueError('Unexpected sequential source')
     result=('var',norm(driver))
    elif ref in ('GND','VCC'):result=('const',int(ref=='VCC'))
    elif re.fullmatch(r'LUT[1-6]',ref) and port=='O':
     width=int(ref[-1]);value=int(init.split("'h")[1],16)
     result=('lut',value,tuple(net_expr(self.pins[cell+'/I'+str(i)]) for i in range(width)))
    else:raise ValueError('Unsupported primitive '+ref+'/'+port)
   visiting.remove(net);return result
  return net_expr(self.pins[pin])
def variables(expr):
 if expr[0]=='var':return {expr[1]}
 if expr[0]=='const':return set()
 return set().union(*(variables(x) for x in expr[2]))
def evaluate(expr,values):
 if expr[0]=='var':return values[expr[1]]
 if expr[0]=='const':return expr[1]
 index=sum(evaluate(x,values)<<i for i,x in enumerate(expr[2]));return (expr[1]>>index)&1

def audit(directory):
 a=Network(directory/'original-network.tsv');b=Network(directory/'masked-network.tsv');checks=[]
 endpoints=['xilinxmultiregimpl'+str(i)+'0_reg/D' for i in (7,8,9)]
 endpoints += [name+'/PRE' for name in ('FDPE','FDPE_2','FDPE_4','FDPE_6','FDPE_8')]
 for pin in endpoints:
  x,y=a.expression(pin),b.expression(pin);inputs=sorted(variables(x)|variables(y))
  if len(inputs)>12:raise ValueError('Truth table cap exceeded')
  for bits in itertools.product((0,1),repeat=len(inputs)):
   values=dict(zip(inputs,bits))
   if evaluate(x,values)!=evaluate(y,values):raise ValueError('Cone mismatch '+pin)
  checks.append({'endpoint':pin,'sequential_cutpoints':inputs,'assignments':1<<len(inputs),'equal':True})
 masks=[]
 for i in range(5):
  old=f'xilinxmultiregimpl{i}0_reg';new=f'xilinxmultiregimpl{i}_{old}'
  od,orr=a.expression(old+'/D'),a.expression(old+'/R')
  nd,nr=b.expression(new+'/D'),b.expression(new+'/R')
  assert orr==('const',0) and od==nd
  assert a.cells[old][0]==b.cells[new][0]=='FDRE'
  assert a.expression(old+'/CE')==b.expression(new+'/CE')==('const',1)
  expected=('var',f'FDPE{("_"+str(2*i+1))}/Q')
  assert nr==expected
  masks.append({'stage':new,'D_unchanged':True,'original_R':0,'masked_R_cutpoint':expected[1],
                'scope':'FDRE nextD is ready AND NOT localReset with CE assumed from separate pin review'})
 return {'status':'EIGHT_COMBINATIONAL_CONES_EQUAL_AND_FIVE_MASK_D_R_MAPPINGS_PASS',
         'cones':checks,'mask_mappings':masks,
         'limits':['Sequential Q cutpoints arbitrary, not sequential equivalence','Not metastability/CDC/reset timing qualification']}
if __name__=='__main__':
 try:print(json.dumps(audit(Path(sys.argv[1])),indent=2))
 except (ValueError,KeyError,IndexError,AssertionError) as e:print('CONE_AUDIT_REFUSED '+str(e),file=sys.stderr);sys.exit(1)
