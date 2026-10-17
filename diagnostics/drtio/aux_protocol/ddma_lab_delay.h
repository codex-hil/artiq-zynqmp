/* Explicit lab-only one-shot arming, no abort/clear writes. LGPL-3.0-or-later. */
#pragma once
#include "ddma_backend.h"
enum {DB_LAB_ARM=72,DB_LAB_ARMED=76,DB_LAB_HOLDING=80,
 DB_LAB_ARM_REJECTED=84,DB_LAB_TRIGGERS=88,DB_LAB_REJECTED=92,DB_LAB_CYCLES=96};
/* Caller must hold device lease and prove a complete idle trace/service ready.
 * Only one arming attempt per boot is allowed by the runtime caller.
 */
static inline int ddma_lab_arm(struct ddma_backend *b,unsigned eligible,unsigned cycles) {
 if(!eligible || !b || !b->read || !b->write || b->faulted ||
    !cycles || cycles>1048576 || db_read(b,DB_ACTIVE) || db_read(b,DB_PENDING) ||
    db_read(b,DB_LAB_ARMED) || db_read(b,DB_LAB_HOLDING) ||
    db_read(b,DB_LAB_TRIGGERS) || db_read(b,DB_LAB_REJECTED) ||
    db_read(b,DB_LAB_ARM_REJECTED) || db_read(b,DB_LAB_CYCLES)!=cycles)return -1;
 db_write(b,DB_LAB_ARM,1);
 return db_read(b,DB_LAB_ARMED)==1 ? 0 : -1;
}
