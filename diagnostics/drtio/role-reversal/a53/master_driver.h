/* LGPL-3.0-or-later. Candidate host-testable driver; not installed firmware. */
#pragma once
#include <stdint.h>
#include "master_regs.h"
struct gm_bus {
 void *context;
 int (*read)(void *,uint32_t,uint32_t *);
 int (*write)(void *,uint32_t,uint32_t);
 int (*fence)(void *);
};
enum gm_error {GM_OK=0,GM_INVALID=-1,GM_PROFILE=-2,GM_IO=-3,
 GM_UNREACHABLE=-4,GM_UNDERFLOW=-5,GM_TIMEOUT=-6,GM_OWNER=-7};
struct gm_result {int error;uint32_t commit_attempted,status_reads;};
/* Caller holds sole CPU/CRI ownership and uses aligned32-bit transactions.
 * Checks are snapshots, not a lock against reset/reconfiguration/owner changes.
 * OK means submitted/status accepted, not proof of physical output execution.
 * On any failure, never retry automatically; commit_attempted means outcome
 * may be unknown, including an error response from the committing MMIO write.
 */
static inline struct gm_result gm_schedule(const struct gm_bus *b,uint32_t destination,
 uint16_t channel,uint64_t timestamp,uint32_t value,uint32_t poll_limit) {
 struct gm_result r={GM_INVALID,0,0};uint32_t v;
 if(!b||!b->read||!b->write||!b->fence||destination>1||!poll_limit||poll_limit>1024)return r;
 const uint32_t addresses[3]={GM_PROFILE_IDENTITY,GM_PROFILE_FINE_WIDTH,GM_PROFILE_COARSE_HZ};
 const uint32_t expected[3]={GM_IDENTITY,3,125000000};
 for(unsigned i=0;i<3;i++) {
  if(b->read(b->context,addresses[i],&v)){r.error=GM_IO;return r;}
  if(v!=expected[i]){r.error=GM_PROFILE;return r;}
 }
 if(b->read(b->context,GM_ROUTING_SELECTED,&v)){r.error=GM_IO;return r;}
 if(v!=0){r.error=GM_OWNER;return r;}
 if(destination) {
  if(b->read(b->context,GM_MASTER_RX_UP,&v)){r.error=GM_IO;return r;}
  if(v!=1){r.error=GM_UNREACHABLE;return r;}
 }
 if(b->write(b->context,GM_KERNEL_TARGET,((destination<<16)|channel)<<8)||b->fence(b->context)||
    b->write(b->context,GM_KERNEL_NOW,(uint32_t)(timestamp>>32))||
    b->write(b->context,GM_KERNEL_NOW+4,(uint32_t)timestamp)||b->fence(b->context)) {
  r.error=GM_IO;return r;
 }
 r.commit_attempted=1;
 if(b->write(b->context,GM_KERNEL_O_DATA+15*4,value)||b->fence(b->context)) {
  r.error=GM_IO;return r;
 }
 for(uint32_t i=0;i<poll_limit;i++) {
  r.status_reads++;
  if(b->read(b->context,GM_KERNEL_O_STATUS,&v)){r.error=GM_IO;return r;}
  if(v&4){r.error=GM_UNREACHABLE;return r;}
  if(v&2){r.error=GM_UNDERFLOW;return r;}
  if(v&~7u){r.error=GM_IO;return r;}
  if(!(v&1)){r.error=GM_OK;return r;}
 }
 r.error=GM_TIMEOUT;return r;
}
