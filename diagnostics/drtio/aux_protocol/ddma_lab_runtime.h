/* Opt-in lab UART arming, LGPL-3.0-or-later. */
#pragma once

#ifdef AUX_DDMA_LAB_DELAY
#include "ddma_lab_delay.h"
static unsigned ddma_lab_attempted;
static void ddma_lab_request(void) {
 unsigned eligible=!ddma_lab_attempted && ddma_ready(0) &&
  ddma.store.complete && !ddma.running && !ddma.status_pending;
 if(!eligible) {xil_printf("AUX_DDMA LAB_ARM REFUSED\r\n");return;}
 xil_printf("AUX_DDMA LAB_BASELINE ar=%u rlast=%u edges=%u\r\n",
  db_read(&ddma_backend,DB_LAB_AR),db_read(&ddma_backend,DB_LAB_RLAST),
  db_read(&ddma_backend,DB_LAB_TTL_EDGES));
 ddma_lab_attempted=1; /* ambiguous writes never retried automatically */
 int result=ddma_lab_arm(&ddma_backend,1,AUX_DDMA_LAB_CYCLES);
 xil_printf("AUX_DDMA LAB_ARM result=%d cycles=%u\r\n",result,AUX_DDMA_LAB_CYCLES);
}
#endif
#ifdef AUX_DDMA_LAB_DELAY
/* Sample real hardware state; never overwrite error/status registers. */
static unsigned ddma_lab_active_seen,ddma_lab_completion_seen;
static void ddma_lab_poll(void) {
 if(!ddma_lab_attempted)return;
 unsigned active=db_read(&ddma_backend,DB_ACTIVE);
 if(!ddma_lab_active_seen && active && db_read(&ddma_backend,DB_LAB_HOLDING) &&
    db_read(&ddma_backend,DB_LAB_TRIGGERS)==1) {
  ddma_lab_active_seen=1;
  xil_printf("AUX_DDMA LAB_ACTIVE id=%u accepted=%u completed=%u triggers=%u\r\n",
   ddma.status.id,db_read(&ddma_backend,DB_ACCEPTED),
   db_read(&ddma_backend,DB_COMPLETED),db_read(&ddma_backend,DB_LAB_TRIGGERS));
 }
 if(ddma_lab_active_seen && !ddma_lab_completion_seen && !active &&
    db_read(&ddma_backend,DB_PENDING)) {
  ddma_lab_completion_seen=1;
  xil_printf("AUX_DDMA LAB_METRICS ar=%u rlast=%u edges=%u\r\n",
   db_read(&ddma_backend,DB_LAB_AR),db_read(&ddma_backend,DB_LAB_RLAST),
   db_read(&ddma_backend,DB_LAB_TTL_EDGES));
  uint64_t ts=db_read64(&ddma_backend,DB_TIMESTAMP);
  xil_printf("AUX_DDMA LAB_COMPLETE id=%u raw=%u channel=%u timestamp=%08x%08x accepted=%u completed=%u faulted=%u\r\n",
   ddma.status.id,db_read(&ddma_backend,DB_ERROR),db_read(&ddma_backend,DB_CHANNEL),
   (unsigned)(ts>>32),(unsigned)ts,db_read(&ddma_backend,DB_ACCEPTED),
   db_read(&ddma_backend,DB_COMPLETED),ddma_backend.faulted);
 }
}
#endif
