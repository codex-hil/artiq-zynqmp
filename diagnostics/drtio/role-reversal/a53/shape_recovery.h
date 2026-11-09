/* SPDX-License-Identifier: LGPL-3.0-or-later
 * Portable candidate sequence, not firmware or a target retry mechanism.
 * Caller must independently stop/withdraw requester traffic and abandon unknown
 * outcomes BEFORE entry. These acknowledgements are obligations, not detection.
 */
#pragma once
#include "reset_driver.h"
#define GSR_SHAPE_FAULT (-20)
struct gsr_result {int error;uint32_t reset_attempted,release_attempted,shape,shape_valid;};
static inline struct gsr_result gsr_recover(const struct gm_bus *b,uint32_t limit,
 uint32_t capability,uint32_t abandoned,uint32_t withdrawn) {
 struct gsr_result r={GR_INVALID,0,0,0,0};
 if(!gr_valid(b,limit)||capability!=1||abandoned!=1||withdrawn!=1)return r;
 uint32_t fault;
 r.error=gr_shape_status(b,capability,&fault);if(r.error)return r;
 r.shape=fault;r.shape_valid=1; /* Diagnostic only: zero does not bypass reset. */
 r.shape_valid=0;
 struct gr_result step=gr_assert_reset(b,limit);
 r.reset_attempted=step.reset_attempted;r.error=step.error;if(r.error)return r;
 r.shape_valid=0;r.error=gr_shape_status(b,capability,&fault);if(r.error)return r;
 r.shape=fault;r.shape_valid=1;
 if(fault){r.error=GSR_SHAPE_FAULT;return r;}
 r.shape_valid=0;step=gr_release_reset(b,limit,abandoned);
 r.release_attempted=step.release_attempted;r.error=step.error;if(r.error)return r;
 r.shape_valid=0;r.error=gr_shape_status(b,capability,&fault);if(r.error)return r;
 r.shape=fault;r.shape_valid=1;r.error=fault?GSR_SHAPE_FAULT:GR_OK;
 return r;
}
/* After any release_attempted, even failure may mean reset is released.
 * GR_OK is only management sequencing + sampled status; target initialization,
 * live-clock qualification and outcome reconciliation remain caller work.
 * No status snapshot can bound a callback blocked in physical MMIO.
 */
