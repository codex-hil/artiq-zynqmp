/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef GENESYS_SPD_XIICPS_H
#define GENESYS_SPD_XIICPS_H
#include "xiicps.h"
#include "xplatform_info.h"
#include "spd_reader.h"
/* Candidate adapter: manually service AMD's master ISR, with no concurrent
 * GIC handler. Caller owns initialized I2C1 and must restore controller/GIC state.
 * No init, bus clear, IRQ routing, clocks, page-baseline detection or retries here.
 */
struct spd_xiicps {
    XIicPs *dev;
    u32 events, expected;
    int active, poisoned;
};
static void spd_amd_event(void *ref,u32 event) {
    struct spd_xiicps *a=ref;a->events|=event;
}
static int spd_amd_idle(void *ctx) {
    struct spd_xiicps *a=ctx;
    if(a->poisoned || a->active) return 0;
    return XIicPs_BusIsBusy(a->dev)==0;
}
static int spd_amd_begin(void *ctx,enum spd_op op,unsigned address,
                         uint8_t *bytes,unsigned length) {
    struct spd_xiicps *a=ctx;
    int read=op==SPD_READ;
    if(!spd_amd_idle(a) || !bytes ||
       !((op==SPD_LOWER_PAGE && address==0x36 && length==1 && bytes[0]==0) ||
         (op==SPD_OFFSET && address==0x51 && length==1 && bytes[0]==0) ||
         (read && address==0x51 && length==128))) return -1;
    a->events=0;a->expected=read?XIICPS_EVENT_COMPLETE_RECV:XIICPS_EVENT_COMPLETE_SEND;
    a->active=1;
    if(read) XIicPs_MasterRecv(a->dev,bytes,(s32)length,(u16)address);
    else XIicPs_MasterSend(a->dev,bytes,(s32)length,(u16)address);
    return 0;
}
static int spd_amd_poll(void *ctx) {
    struct spd_xiicps *a=ctx;
    if(a->poisoned || !a->active) return -1;
    XIicPs_MasterInterruptHandler(a->dev);
    /* Any unexpected event, including completion+error, is terminal. Do not
     * guess controller cleanup after an error; outer recovery is required. */
    if(a->events & ~a->expected) {a->poisoned=1;return -1;}
    if((a->events & a->expected)==0 || XIicPs_BusIsBusy(a->dev)) return 0;
    if((a->expected==XIICPS_EVENT_COMPLETE_RECV && a->dev->RecvByteCount!=0) ||
       (a->expected==XIICPS_EVENT_COMPLETE_SEND && a->dev->SendByteCount!=0)) {
        a->poisoned=1;return -1;
    }
    XIicPs_DisableAllInterrupts(a->dev->Config.BaseAddress);
    a->active=0;return 1;
}
static int spd_amd_bind(struct spd_xiicps *a,XIicPs *dev,int exclusive_no_gic,
                         struct spd_transport *transport) {
    /* Pin scope to ZynqMP. The legacy Zynq receive path contains FIFO waits. */
    if(!a || !dev || !transport || !exclusive_no_gic ||
       XGetPlatform_Info()!=XPLAT_ZYNQ_ULTRA_MP ||
       dev->Config.BaseAddress!=0xff030000U ||
       dev->IsReady!=XIL_COMPONENT_IS_READY || dev->IsRepeatedStart ||
       dev->Is10BitAddr || XIicPs_BusIsBusy(dev)) return -1;
    memset(a,0,sizeof(*a));a->dev=dev;
    XIicPs_SetStatusHandler(dev,a,spd_amd_event);
    *transport=(struct spd_transport){a,spd_amd_begin,spd_amd_poll,spd_amd_idle};
    return 0;
}
#endif
