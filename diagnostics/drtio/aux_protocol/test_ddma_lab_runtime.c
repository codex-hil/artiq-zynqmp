/* Actual lab runtime header with mocked CSR/log IO; LGPL-3.0-or-later. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include "ddma_service.h"
#include "ddma_backend.h"
#define AUX_DDMA_LAB_DELAY
#define AUX_DDMA_LAB_CYCLES 250000u
static struct ddma_service ddma;
static struct ddma_backend ddma_backend;
static unsigned regs[32],writes,active_logs,complete_logs,arm_logs,refused_logs,baseline_logs,metric_logs;
static int ddma_ready(void *p) {(void)p;return !ddma_backend.faulted;}
static uint32_t read_reg(void *p,uintptr_t a) {(void)p;return regs[(a-DDMA_BANK)/4];}
static void write_reg(void *p,uintptr_t a,uint32_t v) {
 (void)p;assert(a==DDMA_BANK+72 && v==1);writes++;regs[76/4]=1;
}
static void log_event(const char *format,...) {
 if(strstr(format,"LAB_BASELINE") || strstr(format,"LAB_METRICS")) {
  va_list args;va_start(args,format);
  unsigned ar=va_arg(args,unsigned),rlast=va_arg(args,unsigned),edges=va_arg(args,unsigned);
  va_end(args);
  if(strstr(format,"LAB_BASELINE")) {baseline_logs++;assert(!ar && !rlast && !edges);}
  else {metric_logs++;assert(ar==2 && rlast==2 && !edges);}
 }
 if(strstr(format,"LAB_ACTIVE"))active_logs++;
 if(strstr(format,"LAB_COMPLETE"))complete_logs++;
 if(strstr(format,"LAB_ARM result"))arm_logs++;
 if(strstr(format,"LAB_ARM REFUSED"))refused_logs++;
}
#define xil_printf log_event
#include "ddma_lab_runtime.h"
int main(void) {
 ddma_backend.read=read_reg;ddma_backend.write=write_reg;
 regs[DB_LAB_CYCLES/4]=250000;
 ddma_lab_request();assert(!writes && refused_logs==1);
 ddma.store.complete=1;ddma_lab_request();assert(writes==1 && arm_logs==1);
 ddma_lab_request();assert(writes==1 && refused_logs==2);
 regs[DB_ACTIVE/4]=1;ddma_lab_poll();assert(!active_logs);
 regs[DB_LAB_HOLDING/4]=1;ddma_lab_poll();assert(!active_logs);
 regs[DB_LAB_TRIGGERS/4]=1;ddma_lab_poll();ddma_lab_poll();assert(active_logs==1);
 regs[DB_ACTIVE/4]=0;ddma_lab_poll();assert(!complete_logs);
 regs[DB_LAB_AR/4]=2;regs[DB_LAB_RLAST/4]=2;
 regs[DB_PENDING/4]=1;regs[DB_ERROR/4]=4;ddma_backend.faulted=1;
 ddma_lab_poll();ddma_lab_poll();assert(complete_logs==1 && baseline_logs==1 && metric_logs==1);
 puts("DDMA_LAB_RUNTIME_OFFLINE_PASS readiness, one attempt, active-hold proof, completion once");
}
