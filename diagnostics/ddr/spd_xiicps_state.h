/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef GENESYS_SPD_XIICPS_STATE_H
#define GENESYS_SPD_XIICPS_STATE_H
#include "spd_xiicps.h"
struct spd_amd_snapshot {
    XIicPs software;
    u32 control, timeout, interrupt_mask;
    int valid;
};
static int spd_amd_quiet(XIicPs *dev) {
    UINTPTR base=dev->Config.BaseAddress;
    return !XIicPs_BusIsBusy(dev) &&
      !(XIicPs_ReadReg(base,XIICPS_SR_OFFSET)&(XIICPS_SR_RXDV_MASK|XIICPS_SR_TXDV_MASK)) &&
      XIicPs_ReadReg(base,XIICPS_TRANS_SIZE_OFFSET)==0 &&
      XIicPs_ReadReg(base,XIICPS_ISR_OFFSET)==0 &&
      !(XIicPs_ReadReg(base,XIICPS_CR_OFFSET)&(XIICPS_CR_HOLD_MASK|XIICPS_CR_CLR_FIFO_MASK));
}
/* Exclusive CPU/peripheral ownership and absent GIC dispatch are external
 * preconditions, not proven by these register checks. No write before admission.
 */
static int spd_amd_snapshot(struct spd_amd_snapshot *s,XIicPs *dev,int exclusive_no_gic) {
    if(!s)return -1;
    memset(s,0,sizeof(*s));
    if(!dev || !exclusive_no_gic || dev->Config.BaseAddress!=0xff030000U ||
       dev->IsReady!=XIL_COMPONENT_IS_READY || dev->SendByteCount!=0 ||
       dev->RecvByteCount!=0 || !spd_amd_quiet(dev))return -1;
    memcpy(&s->software,dev,sizeof(*dev));
    s->control=XIicPs_ReadReg(dev->Config.BaseAddress,XIICPS_CR_OFFSET);
    s->timeout=XIicPs_ReadReg(dev->Config.BaseAddress,XIICPS_TIME_OUT_OFFSET);
    s->interrupt_mask=XIicPs_ReadReg(dev->Config.BaseAddress,XIICPS_IMR_OFFSET)&XIICPS_IXR_ALL_INTR_MASK;
    s->valid=1;return 0;
}
static int spd_amd_restore(struct spd_amd_snapshot *s,struct spd_xiicps *a,int exclusive_no_gic) {
    if(!s || !s->valid || !a || !a->dev || !exclusive_no_gic || a->active || a->poisoned ||
       a->dev->Config.BaseAddress!=s->software.Config.BaseAddress || !spd_amd_quiet(a->dev))return -1;
    XIicPs *dev=a->dev;UINTPTR base=dev->Config.BaseAddress;
    XIicPs_DisableAllInterrupts(base);
    XIicPs_WriteReg(base,XIICPS_CR_OFFSET,s->control);
    XIicPs_WriteReg(base,XIICPS_TIME_OUT_OFFSET,s->timeout);
    memcpy(dev,&s->software,sizeof(*dev));
    XIicPs_EnableInterrupts(base,(~s->interrupt_mask)&XIICPS_IXR_ALL_INTR_MASK);
    if(XIicPs_ReadReg(base,XIICPS_CR_OFFSET)!=s->control ||
       XIicPs_ReadReg(base,XIICPS_TIME_OUT_OFFSET)!=s->timeout ||
       (XIicPs_ReadReg(base,XIICPS_IMR_OFFSET)&XIICPS_IXR_ALL_INTR_MASK)!=s->interrupt_mask ||
       !spd_amd_quiet(dev)) {s->valid=0;a->poisoned=1;return -1;}
    /* Consume snapshot/adapter so a second restore cannot overwrite later work. */
    s->valid=0;a->poisoned=1;a->dev=NULL;return 0;
}
#endif
