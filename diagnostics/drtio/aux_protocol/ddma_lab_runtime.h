/* Opt-in lab UART arming, LGPL-3.0-or-later. */
#pragma once

#ifdef AUX_DDMA_LAB_DELAY
#include "ddma_lab_delay.h"
static unsigned ddma_lab_attempted;
static void ddma_lab_request(void) {
 unsigned eligible=!ddma_lab_attempted && ddma_ready(0) &&
  ddma.store.complete && !ddma.running && !ddma.status_pending;
 if(!eligible) {xil_printf("AUX_DDMA LAB_ARM REFUSED\r\n");return;}
 ddma_lab_attempted=1; /* ambiguous writes never retried automatically */
 int result=ddma_lab_arm(&ddma_backend,1,AUX_DDMA_LAB_CYCLES);
 xil_printf("AUX_DDMA LAB_ARM result=%d cycles=%u\r\n",result,AUX_DDMA_LAB_CYCLES);
}
#endif
