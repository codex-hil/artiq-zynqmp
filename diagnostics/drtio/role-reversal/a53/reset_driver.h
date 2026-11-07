/* SPDX-License-Identifier: LGPL-3.0-or-later
 * Portable management API, not installed recovery firmware. Caller must run in
 * an independently responsive context and preserve target unknown outcomes.
 */
#pragma once
#include "master_driver.h"
#define GR_BASE 0xb0000000u
#define GR_ID 0x47524d31u
enum gr_error {GR_OK=0,GR_INVALID=-1,GR_PROFILE=-2,GR_IO=-3,GR_TIMEOUT=-4};
struct gr_result {int error;uint32_t reset_attempted,release_attempted,status_reads;};
static inline int gr_valid(const struct gm_bus *b,uint32_t limit) {
 return b&&b->read&&b->write&&b->fence&&limit&&limit<=1024;
}
static inline int gr_profile(const struct gm_bus *b) {
 uint32_t v;if(b->read(b->context,GR_BASE,&v))return GR_IO;
 return v==GR_ID?GR_OK:GR_PROFILE;
}
static inline int gr_poll(const struct gm_bus *b,uint32_t mask,uint32_t want,
 uint32_t limit,struct gr_result *r) {
 for(uint32_t i=0;i<limit;i++) {
  uint32_t v;r->status_reads++;
  if(b->read(b->context,GR_BASE+8,&v)||v&~7u)return GR_IO;
  if((v&mask)==want)return GR_OK;
 }
 return GR_TIMEOUT;
}
static inline struct gr_result gr_assert_reset(const struct gm_bus *b,uint32_t limit) {
 struct gr_result r={GR_INVALID,0,0,0};
 if(!gr_valid(b,limit))return r;
 if((r.error=gr_profile(b)))return r;
 r.reset_attempted=1; /* write may execute even if callback reports error */
 if(b->write(b->context,GR_BASE+4,1)||b->fence(b->context)){r.error=GR_IO;return r;}
 r.error=gr_poll(b,5,1,limit,&r);return r;
}
/* abandoned must be explicit caller acknowledgement, never inferred from reset.
 * Success means admission reopened, target protocol reinitialization still needed.
 * Any failure after release_attempted may have released reset: do not assume held.
 */
static inline struct gr_result gr_release_reset(const struct gm_bus *b,uint32_t limit,
 uint32_t abandoned) {
 struct gr_result r={GR_INVALID,0,0,0};
 if(!gr_valid(b,limit)||abandoned!=1)return r;
 if((r.error=gr_profile(b)))return r;
 if(b->write(b->context,GR_BASE+4,0)||b->fence(b->context)){r.error=GR_IO;return r;}
 if((r.error=gr_poll(b,3,3,limit,&r)))return r;
 r.release_attempted=1;
 if(b->write(b->context,GR_BASE+4,2)||b->fence(b->context)){r.error=GR_IO;return r;}
 r.error=gr_poll(b,5,4,limit,&r);return r;
}
