/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef GENESYS_SPD_PAGE_TRANSFER_H
#define GENESYS_SPD_PAGE_TRANSFER_H
#include "spd_xiicps_state.h"
#include "spd_page.h"
enum spd_page_operation { SPD_QUERY_PAGE, SPD_SELECT_ZERO, SPD_SELECT_ONE };
struct spd_page_transfer {
    XIicPs *dev; enum spd_page_operation op; enum spd_page page;
    u32 raw_irq, events; uint8_t byte;
    uint64_t deadline,last_now; unsigned polls;
    int active, stopped, failed;
};
static void spd_page_event(void *ref,u32 events) {
    struct spd_page_transfer *q=ref;q->events|=events;
}
static void spd_page_fail(struct spd_page_transfer *q) {
    q->failed=1;q->stopped=1;q->page=SPD_PAGE_UNKNOWN;
    /* Active remains set. Outer restoration required; no abort/clear/retry. */
}
static int spd_page_begin(struct spd_page_transfer *q,XIicPs *dev,
                          enum spd_page_operation op,uint64_t now,
                          int exclusive_no_gic,int independent_identity) {
    /* Caller zero-initializes once; failed/active objects cannot be reused. */
    if(!q || q->active || q->failed)return -1;
    memset(q,0,sizeof(*q));q->page=SPD_PAGE_UNKNOWN;q->last_now=now;
    if(!dev || !exclusive_no_gic || !independent_identity ||
       XGetPlatform_Info()!=XPLAT_ZYNQ_ULTRA_MP ||
       dev->Config.BaseAddress!=0xff030000U || dev->IsReady!=XIL_COMPONENT_IS_READY ||
       dev->IsRepeatedStart || dev->Is10BitAddr || dev->SendByteCount || dev->RecvByteCount ||
       !spd_amd_quiet(dev) || op<SPD_QUERY_PAGE || op>SPD_SELECT_ONE || now>UINT64_MAX-100000) {
        spd_page_fail(q);return -1;
    }
    q->dev=dev;q->op=op;q->deadline=now+100000;q->active=1;
    XIicPs_SetStatusHandler(dev,q,spd_page_event);
    if(op==SPD_QUERY_PAGE)XIicPs_MasterRecv(dev,&q->byte,1,0x36);
    else XIicPs_MasterSend(dev,&q->byte,1,op==SPD_SELECT_ZERO?0x36:0x37);
    return 0;
}
static void spd_page_tick(struct spd_page_transfer *q,uint64_t now) {
    if(q->stopped)return;
    if(now<q->last_now || now>=q->deadline || ++q->polls>10000) {spd_page_fail(q);return;}
    q->last_now=now;XIicPs *dev=q->dev;UINTPTR base=dev->Config.BaseAddress;
    q->raw_irq|=XIicPs_ReadReg(base,XIICPS_ISR_OFFSET);
    XIicPs_MasterInterruptHandler(dev);
    if(!q->events)return;
    /* Unexpected events fail immediately, even when the bus is busy. */
    if(q->op==SPD_QUERY_PAGE) {
        if(q->events!=XIICPS_EVENT_COMPLETE_RECV && q->events!=(XIICPS_EVENT_NACK|XIICPS_EVENT_ERROR)) {
            spd_page_fail(q);return;
        }
    } else if(q->events!=XIICPS_EVENT_COMPLETE_SEND) {spd_page_fail(q);return;}
    if(XIicPs_BusIsBusy(dev))return;
    u32 sr=XIicPs_ReadReg(base,XIICPS_SR_OFFSET),cr=XIicPs_ReadReg(base,XIICPS_CR_OFFSET);
    if((sr&(XIICPS_SR_RXDV_MASK|XIICPS_SR_TXDV_MASK)) ||
       (cr&(XIICPS_CR_HOLD_MASK|XIICPS_CR_CLR_FIFO_MASK)) ||
       XIicPs_ReadReg(base,XIICPS_ISR_OFFSET)!=0) {spd_page_fail(q);return;}
    if(q->op==SPD_QUERY_PAGE) {
        if(dev->RecvByteCount<0 || dev->RecvByteCount>1) {spd_page_fail(q);return;}
        struct spd_page_reply reply={.address=0x36,.requested=1,.received=1-dev->RecvByteCount,
          .raw_irq=q->raw_irq,.events=q->events,.exclusive_route_proven=1,
          .independent_spd_identity_proven=1,.bus_idle=1,.fifo_empty=1};
        q->page=spd_classify_page(reply);
        if(q->page==SPD_PAGE_UNKNOWN) {spd_page_fail(q);return;}
        unsigned expected=q->page==SPD_PAGE_ONE?1U:0U;
        if(XIicPs_ReadReg(base,XIICPS_TRANS_SIZE_OFFSET)!=expected) {spd_page_fail(q);return;}
        XIicPs_DisableAllInterrupts(base);
        /* Exact protocol NACK terminates this 1-byte query with zero payload.
         * Retire its unused count only after idle/empty/status proof. No FIFO
         * clear, abort, reset, retry or generic error recovery is performed. */
        if(expected)XIicPs_WriteReg(base,XIICPS_TRANS_SIZE_OFFSET,0);
        if(XIicPs_ReadReg(base,XIICPS_TRANS_SIZE_OFFSET)!=0) {spd_page_fail(q);return;}
        dev->RecvByteCount=0;dev->CurrByteCount=0;dev->RecvBufferPtr=NULL;
    } else {
        if(dev->SendByteCount!=0 || q->raw_irq!=XIICPS_IXR_COMP_MASK ||
           XIicPs_ReadReg(base,XIICPS_TRANS_SIZE_OFFSET)!=0) {spd_page_fail(q);return;}
        XIicPs_DisableAllInterrupts(base);
        dev->SendBufferPtr=NULL;
        /* A successful write is not page confirmation; page stays UNKNOWN. */
    }
    if(!spd_amd_quiet(dev)) {spd_page_fail(q);return;}
    q->active=0;q->stopped=1;
}
#endif
