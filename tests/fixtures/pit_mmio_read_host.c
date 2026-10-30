/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Synthetic process-local anonymous memory, never /dev/mem or real hardware. */
#define _GNU_SOURCE
#include <sys/mman.h>
#include <assert.h>
#include <string.h>
#include "pit_mmio_read.h"
#include "pit_ro_adapter.h"
int main(void) {
 void *page=mmap((void *)(uintptr_t)0xffd40000,4096,PROT_READ|PROT_WRITE,
                MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
 assert(page!=MAP_FAILED);
 uint32_t *words=page, output=0xabcdef01;
 for(unsigned i=0;i<1024;i++)words[i]=0x55550000+i;
 uint32_t before[1024];memcpy(before,page,4096);
 assert(pit_mmio_read(NULL,0xffd40040,&output)==-1 && output==0xabcdef01);
 assert(pit_mmio_read(NULL,0xffd40045,&output)==-1 && output==0xabcdef01);
 assert(pit_mmio_read(NULL,0xffd50044,&output)==-1 && output==0xabcdef01);
 assert(pit_mmio_read((void *)1,0xffd40044,&output)==-1);
 assert(pit_mmio_read(NULL,0xffd40044,NULL)==-1);
 struct pit_ro_adapter adapter={0};assert(pit_ro_prepare(&adapter,pit_mmio_read,NULL)==0);
 for(unsigned i=0;i<8;i++) {
  uint32_t address=0xffd40044+(i%4)*16;
  assert(pit_ro_read(&adapter,address,&output)==0);
  assert(output==words[(address-0xffd40000)/4]);
 }
 assert(adapter.attempted==8);
 assert(pit_ro_read(&adapter,0xffd40044,&output)==-1);
 assert(memcmp(before,page,4096)==0);
 assert(munmap(page,4096)==0);
 return 0;
}
