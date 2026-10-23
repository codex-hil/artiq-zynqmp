/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pattern.h"
static int valid(uint64_t address) {
 return !(address & 7U) && (address < UINT64_C(0x80000000) ||
       (address >= UINT64_C(0x800000000) && address < UINT64_C(0x880000000)));
}
static uint64_t tag(uint64_t address, uint32_t phase) {
 if (phase==0) return 0;
 if (phase==1) return UINT64_MAX;
 uint64_t v=address ^ UINT64_C(0xa53dd4c0dec0ffee);
 return phase==2 ? v : ~v;
}
int ddr_pattern(const uint64_t *addresses, uint32_t count,
                const struct ddr_io *io, struct ddr_report *r) {
 if (!r) return DDR_ARGUMENT;
 *r=(struct ddr_report){0};
 if (!addresses || !io || !io->write || !io->read || !io->barrier || !count || count>8192) {
  r->error=DDR_ARGUMENT;return r->error;
 }
 /* Validate whole list before the first callback, including duplicate probes. */
 for (uint32_t i=0;i<count;i++) {
  if (!valid(addresses[i])) {r->error=DDR_ARGUMENT;return r->error;}
  for (uint32_t j=0;j<i;j++) if (addresses[i]==addresses[j]) {r->error=DDR_ARGUMENT;return r->error;}
 }
 for (uint32_t phase=0;phase<4;phase++) {
  r->phase=phase;
  for (uint32_t i=0;i<count;i++) {
   r->address=addresses[i];r->expected=tag(r->address,phase);
   if (io->write(io->context,r->address,r->expected)) {r->error=DDR_WRITE;return r->error;}
   r->writes++;
  }
  if (io->barrier(io->context)) {r->error=DDR_BARRIER;return r->error;}
  for (uint32_t i=0;i<count;i++) {
   r->address=addresses[i];r->expected=tag(r->address,phase);
   if (io->read(io->context,r->address,&r->actual)) {r->error=DDR_READ;return r->error;}
   r->reads++;
   if (r->actual!=r->expected) {r->error=DDR_MISMATCH;return r->error;}
  }
 }
 return DDR_OK;
}
