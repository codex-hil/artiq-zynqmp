/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "master_network_admission.h"
#include "master_guarded_start.h"
static unsigned calls,cases;
/* A revoked path must never enter IO or a codec. These are refusal sentinels,
 * not substitute codecs or a healthy-path hardware model. */
static int read_bus(void *c,uint32_t a,uint32_t *v){(void)c;(void)a;(void)v;calls++;return -1;}
static int write_bus(void *c,uint32_t a,uint32_t v){(void)c;(void)a;(void)v;calls++;return -1;}
static int fence_bus(void *c){(void)c;calls++;return -1;}
int32_t aux_master_leaf_encode(uint32_t a,uint32_t b,uint8_t *c,size_t d){(void)a;(void)b;(void)c;(void)d;calls++;return -1;}
int32_t aux_master_star_path_encode(uint32_t a,uint8_t *b,size_t c){(void)a;(void)b;(void)c;calls++;return -1;}
int32_t aux_master_control_encode(uint32_t a,uint32_t b,uint8_t *c,size_t d){(void)a;(void)b;(void)c;(void)d;calls++;return -1;}
int32_t aux_master_control_decode(const uint8_t *a,size_t b){(void)a;(void)b;calls++;return -1;}
int32_t aux_master_routing_ack_decode(const uint8_t *a,size_t b){(void)a;(void)b;calls++;return -1;}
static struct mfo_gate grant(void){struct mfo_gate g={0};mfo_init(&g);assert(!mfo_fresh_epoch(&g,1,15));assert(!mfo_request_master(&g));assert(!mfo_grant_master(&g,7));return g;}
int main(void){
 for(unsigned receipt=0;receipt<16;receipt++)for(unsigned fault=0;fault<2;fault++){
  struct mfo_gate g=grant();struct mne_policy p={0};uint64_t ticket=g.ticket;
  int r=mne_begin(&p,&g,ticket,9,receipt,(int)fault);
  if(receipt==7&&!fault){assert(!r&&mne_ready(&p));g.state=MFO_HELD;assert(!mne_observe(&p,9,7,0)&&mne_ready(&p));}
  else {assert(r==MNE_UNSAFE&&!mne_ready(&p)&&g.state==MFO_FAULT&&g.ticket==ticket&&g.owner==MFO_MASTER_OWNER);assert(mne_observe(&p,9,7,0)==r);}
  assert(mne_begin(&p,&g,ticket,9,7,0)==MNE_INVALID);cases++;
 }
 for(unsigned phase=0;phase<3;phase++)for(unsigned fault=0;fault<5;fault++){
  struct mfo_gate g=grant();struct mne_policy p={0};assert(!mne_begin(&p,&g,g.ticket,9,7,0));
  struct mfg_start s={.gate=&g,.ticket=g.ticket,.epoch=g.epoch,.started=1,.phase=(enum mfg_phase)phase};
  s.mm.bus=(struct mm_bus){0,read_bus,write_bus,fence_bus};s.mm.bound=1;
  uint64_t generation=fault==0?10:fault==1?8:fault==2?0:9;
  int r=mne_observe(&p,generation,fault==3?3:7,fault==4?1:0);assert(r==MNE_UNSAFE);
  assert(!mne_ready(&p)&&mfg_step(&s)==r&&!calls&&s.mm.failed&&!s.mm.bound&&g.state==MFO_FAULT);
  assert(mfo_worker_dispatch(&g)==MFO_BUSY&&mfo_release_master(&g,g.ticket,7)==MFO_BUSY);cases++;
 }
 for(int error=-1;error>=-5;error--){
  struct mfo_gate g=grant();struct mne_policy p={0};assert(!mne_begin(&p,&g,g.ticket,9,7,0));assert(mfo_fault(&g,error)==error);
  assert(mne_observe(&p,10,0,1)==error&&g.error==error&&!mne_ready(&p));cases++;
 }
 {struct mfo_gate g=grant();struct mne_policy p={0};assert(!mne_begin(&p,&g,g.ticket,9,7,0));mfo_fault(&g,-99);
  assert(!mfo_fresh_epoch(&g,2,15)&&!mfo_request_master(&g)&&!mfo_grant_master(&g,7));struct mfo_gate before=g;
  assert(mne_observe(&p,10,0,1)==MNE_STALE&&!mne_ready(&p));assert(g.state==before.state&&g.ticket==before.ticket&&g.epoch==before.epoch&&g.error==before.error);cases++;
 }
 {struct mfo_gate g=grant();struct mne_policy p={0};assert(mne_begin(&p,&g,g.ticket,0,7,0)==MNE_UNSAFE&&!mne_ready(&p));cases++;}
 {struct mne_policy p={0};assert(mne_observe(&p,1,7,0)==MNE_INVALID&&!mne_ready(&p)&&mne_begin(0,0,0,0,0,0)==MNE_INVALID);cases++;}
 {struct mfo_gate g=grant();struct mne_policy p={0};assert(!mne_begin(&p,&g,g.ticket,9,7,0));g.state=MFO_FAULT;g.error=0;
  assert(mne_observe(&p,9,7,0)==MNE_UNSAFE&&!mne_ready(&p));cases++;}
 {struct mfo_gate g=grant();struct mne_policy p={0};g.epoch=0;assert(mne_begin(&p,&g,g.ticket,9,7,0)==MNE_INVALID&&!p.started);cases++;}
 printf("NETWORK_ADMISSION_POLICY_PASS cases=%u io_or_codec_calls=%u\n",cases,calls);return 0;
}
