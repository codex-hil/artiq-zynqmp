/* AUX service binding to actual A53 DMA; opt-in laboratory subset.
 * LGPL-3.0-or-later. Included after send/MMIO/reset helpers.
 */
#pragma once
#include "ddma_service.h"
#include "tsc_a53.h"
static struct ddma_service ddma;
static struct ddma_backend ddma_backend;
static struct tsc_reader ddma_clock;
static uint64_t ddma_started_ns;
static uint32_t ddma_epoch;
static int ddma_ready(void *context) {
 (void)context;
 return !ddma_backend.faulted && reset_backend_ready() &&
  !rd(REG_AUX_RTIO_RESET_REQUEST) && !rd(REG_AUX_RTIO_RESET_APPLIED) &&
  !rd(REG_AUX_RTIO_ERROR_FLAGS) && rd(REG_AUX_TSC_LOAD_COUNT);
}
static int ddma_time(void *context,uint64_t *value) {
 (void)context;return tsc_read_upper(&ddma_clock,value);
}
static void ddma_fatal(void) {
 xil_printf("AUX_DDMA FAIL_CLOSED\r\n");wr(REG_MONITOR_TX_ENABLE,0);aux_panic();
}
static void ddma_init(void) {
 ddma_service_init(&ddma);ddma_clock=tsc_a53_bind(0,ddma_ready);
 ddma_backend=ddma_a53_bind(0,ddma_time,ddma_ready);
}
static void ddma_send(unsigned kind,const struct ddma_packet *packet) {
 uint8_t bytes[1024];int size=aux_ddma_encode(kind,packet,bytes,sizeof(bytes));
 if(size<0 || send(bytes,size))ddma_fatal();
}
static void ddma_poll(void) {
 if(ddma.running) {
  uint64_t now;
  if(db_read(&ddma_backend,DB_PENDING) && !db_read(&ddma_backend,DB_ACTIVE)) {
   unsigned error=db_read(&ddma_backend,DB_ERROR);
   if(ddma_service_complete(&ddma,error,db_read(&ddma_backend,DB_CHANNEL),
         db_read64(&ddma_backend,DB_TIMESTAMP)))ddma_fatal();
   if(error)ddma_backend.faulted=1; /* no unqualified post-error reuse */
  } else if(!ddma_ready(0) || rd(REG_AUX_TSC_LOAD_COUNT)!=ddma_epoch ||
    tsc_a53_monotonic_ns(0,&now) || now<ddma_started_ns ||
    now-ddma_started_ns>2000000000ull)ddma_fatal();
 }
 if(ddma.status_pending) {
  ddma_send(0xb6,&ddma.status);
  xil_printf("AUX_DDMA STATUS id=%u error=%u\r\n",ddma.status.id,ddma.status.error);
  if(ddma_service_status_sent(&ddma))ddma_fatal();
 }
}
static int ddma_handle(unsigned kind,const struct ddma_packet *packet,unsigned ready) {
 struct ddma_packet reply;
 if(kind==0xb0)xil_printf("AUX_DDMA UPLOAD id=%u status=%u bytes=%u\r\n",
   packet->id,packet->status,packet->length);
 unsigned response=ddma_service_request(&ddma,kind,packet,&reply,ready && ddma_ready(0),
   ddma_backend_start,&ddma_backend);
 if(!response)return 0;
 if(kind==0xb4 && reply.succeeded) {
  ddma_epoch=rd(REG_AUX_TSC_LOAD_COUNT);
  if(tsc_a53_monotonic_ns(0,&ddma_started_ns))ddma_fatal();
 }
 ddma_send(response,&reply);
 xil_printf("AUX_DDMA REPLY kind=%u id=%u succeeded=%u\r\n",response,packet->id,reply.succeeded);
 if(ddma_backend.faulted && !ddma.running)ddma_fatal();
 return 1;
}
