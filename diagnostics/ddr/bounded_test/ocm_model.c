/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pattern.h"
/* Deliberately OCM-backed model: addresses are tags, never dereferenced. */
static const uint64_t probes[]={0x40000000,0x7ffffff8,0x800000000,0x87ffffff8};
static uint64_t cells[4];
struct ddr_report model_report;
volatile uint32_t model_result;
static int index_of(uint64_t address) {
 for (unsigned i=0;i<4;i++) if (probes[i]==address) return (int)i;
 return -1;
}
static int write_model(void *context,uint64_t address,uint64_t value) {
 (void)context;int i=index_of(address);if (i<0) return 1;
 cells[i]=value;return 0;
}
static int read_model(void *context,uint64_t address,uint64_t *value) {
 (void)context;int i=index_of(address);if (i<0) return 1;
 *value=cells[i];return 0;
}
static int barrier_model(void *context) {(void)context;return 0;}
int ocm_model_main(void) {
 const struct ddr_io io={0,write_model,read_model,barrier_model};
 model_result=(uint32_t)ddr_pattern(probes,4,&io,&model_report);
 return (int)model_result;
}
