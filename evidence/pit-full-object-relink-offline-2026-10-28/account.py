# SPDX-License-Identifier: LGPL-3.0-or-later
"""Exact timestamp difference accounting, not image equivalence or admission."""
def account(old,new,fields):
 if old[:2]!=new[:2] or len(old[2])!=len(new[2]):raise ValueError('changed ELF machine/entry/segment count')
 expected={};locations=[]
 for label,before,after in fields:
  if len(before)!=len(after):raise ValueError('changed timestamp length')
  matches=[]
  for si,s in enumerate(old[2]):
   start=0
   while True:
    at=s['payload'].find(before,start)
    if at<0:break
    matches.append((si,at));start=at+1
  if len(matches)!=1:raise ValueError('timestamp must occur uniquely')
  si,at=matches[0];locations.append({'field':label,'address':hex(old[2][si]['address']+at),'bytes':len(before)})
  if new[2][si]['payload'][at:at+len(after)]!=after:raise ValueError('unexpected timestamp value')
  for j,(a,b) in enumerate(zip(before,after)):
   if a!=b:expected[si,at+j]=(a,b)
 actual={}
 for si,(a,b) in enumerate(zip(old[2],new[2])):
  if {k:v for k,v in a.items() if k!='payload'}!={k:v for k,v in b.items() if k!='payload'}:raise ValueError('segment metadata changed')
  if len(a['payload'])!=len(b['payload']):raise ValueError('payload length changed')
  for i,(u,v) in enumerate(zip(a['payload'],b['payload'])):
   if u!=v:actual[si,i]=(u,v)
 if actual!=expected:raise ValueError('unaccounted load byte difference')
 return {'status':'EXACT_TIMESTAMP_DIFFERENCES_ACCOUNTED_NOT_IDENTICAL','changed_bytes':len(actual),'fields':locations,'deployable':False,'hardware_executed':False}
