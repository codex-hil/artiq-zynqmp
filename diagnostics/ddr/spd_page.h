/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef GENESYS_SPD_PAGE_H
#define GENESYS_SPD_PAGE_H
#include "xiicps.h"
enum spd_page { SPD_PAGE_UNKNOWN=-1, SPD_PAGE_ZERO=0, SPD_PAGE_ONE=1 };
struct spd_page_reply {
    unsigned address, requested, received;
    u32 raw_irq, events;
    int exclusive_route_proven, independent_spd_identity_proven;
    int bus_idle, fifo_empty, timed_out;
};
/* Pure classifier for the EE1004 read-page-address operation only.
 * Flags represent external evidence; this function cannot establish identity.
 * No general NACK exception, I2C operation or driver-state reset is performed.
 */
static inline enum spd_page spd_classify_page(struct spd_page_reply r) {
    if(r.address!=0x36 || r.requested!=1 ||
       !r.exclusive_route_proven || !r.independent_spd_identity_proven ||
       !r.bus_idle || !r.fifo_empty || r.timed_out)return SPD_PAGE_UNKNOWN;
    if(r.received==1 && r.events==XIICPS_EVENT_COMPLETE_RECV &&
       (r.raw_irq&XIICPS_IXR_COMP_MASK) &&
       !(r.raw_irq&~(XIICPS_IXR_COMP_MASK|XIICPS_IXR_DATA_MASK)))return SPD_PAGE_ZERO;
    if(r.received==0 && r.raw_irq==XIICPS_IXR_NACK_MASK &&
       r.events==(XIICPS_EVENT_NACK|XIICPS_EVENT_ERROR))return SPD_PAGE_ONE;
    return SPD_PAGE_UNKNOWN;
}
static inline int spd_page_select_address(enum spd_page saved) {
    return saved==SPD_PAGE_ZERO?0x36:saved==SPD_PAGE_ONE?0x37:-1;
}
static inline int spd_page_restore_confirmed(enum spd_page saved,struct spd_page_reply reply) {
    return saved!=SPD_PAGE_UNKNOWN && spd_classify_page(reply)==saved;
}
#endif
