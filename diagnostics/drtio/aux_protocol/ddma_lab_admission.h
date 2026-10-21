/* Lab-only callback telemetry around unchanged backend. LGPL-3.0-or-later. */
#pragma once
#include "ddma_backend.h"
struct ddma_lab_admission {
 struct ddma_backend *original;
 unsigned step,time_calls,ready_calls;
 int time_result,ready_result;
 uint64_t now;
 uintptr_t address;
 uint32_t value;
};
static uint32_t dla_read(void *context,uintptr_t address) {
 struct ddma_lab_admission *t=context;t->step=3;t->address=address;
 t->value=t->original->read(t->original->context,address);return t->value;
}
static void dla_write(void *context,uintptr_t address,uint32_t value) {
 struct ddma_lab_admission *t=context;t->step=4;t->address=address;t->value=value;
 t->original->write(t->original->context,address,value);
}
static int dla_copy(void *context,uintptr_t address,const uint8_t *bytes,size_t length) {
 struct ddma_lab_admission *t=context;t->step=5;
 return t->original->copy(t->original->context,address,bytes,length);
}
static void dla_flush(void *context,uintptr_t address,size_t length) {
 struct ddma_lab_admission *t=context;t->step=6;
 t->original->flush(t->original->context,address,length);
}
static int dla_time(void *context,uint64_t *value) {
 struct ddma_lab_admission *t=context;t->step=2;t->time_calls++;
 t->time_result=t->original->time(t->original->context,value);
 if(!t->time_result)t->now=*value;
 return t->time_result;
}
static int dla_ready(void *context) {
 struct ddma_lab_admission *t=context;t->step=1;t->ready_calls++;
 t->ready_result=t->original->ready(t->original->context);return t->ready_result;
}
static void dla_delay(void *context) {
 struct ddma_lab_admission *t=context;t->step=7;
 t->original->delay(t->original->context);
}
static int ddma_lab_admission_start(void *context,const uint8_t *bytes,size_t length,uint64_t timestamp) {
 struct ddma_backend *b=context;struct ddma_lab_admission t={0};int result;
 /* Preserve the original missing-callback admission checks, never mask NULL. */
 if(!b || !b->read || !b->write || !b->copy || !b->flush || !b->time || !b->ready || !b->delay)
  return ddma_backend_start(context,bytes,length,timestamp);
 t.original=b;
 struct ddma_backend wrapped={&t,dla_read,dla_write,dla_copy,dla_flush,dla_time,dla_ready,dla_delay,b->faulted};
 result=ddma_backend_start(&wrapped,bytes,length,timestamp);
 b->faulted=wrapped.faulted;
 /* No UART output on accepted start; never add MMIO/time reads for telemetry. */
 if(result<0)xil_printf("AUX_DDMA LAB_ADMISSION_REJECT step=%u ready_calls=%u ready=%d time_calls=%u time_result=%d now=%08x%08x requested=%08x%08x address=%08x value=%u faulted=%u\r\n",
  t.step,t.ready_calls,t.ready_result,t.time_calls,t.time_result,
  (unsigned)(t.now>>32),(unsigned)t.now,(unsigned)(timestamp>>32),(unsigned)timestamp,
  (unsigned)t.address,t.value,b->faulted);
 return result;
}
