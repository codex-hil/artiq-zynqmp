/* Bounded DDR/cache/CSR adapter; LGPL-3.0-or-later.
 * Caller supplies live MMIO/cache/time/readiness functions, no fake time.
 * Target map must be validated against these immutable diagnostic addresses.
 */
#pragma once
#include <stdint.h>
#include <stddef.h>
#define DDMA_BANK ((uintptr_t)0xa0002000u)
#define DDMA_ARENA ((uintptr_t)0x22000000u)
enum {DB_ADDRESS=0,DB_OFFSET=8,DB_BUDGET=16,DB_WATCHDOG=20,DB_START=24,
 DB_ABORT=28,DB_CLEAR=32,DB_ACTIVE=36,DB_PENDING=40,DB_REJECT=44,
 DB_ERROR=48,DB_CHANNEL=52,DB_TIMESTAMP=56,DB_ACCEPTED=64,DB_COMPLETED=68};
struct ddma_backend {
 void *context;
 uint32_t (*read)(void *,uintptr_t);
 void (*write)(void *,uintptr_t,uint32_t);
 int (*copy)(void *,uintptr_t,const uint8_t *,size_t);
 void (*flush)(void *,uintptr_t,size_t);
 int (*time)(void *,uint64_t *);
 int (*ready)(void *);
 void (*delay)(void *);
 unsigned faulted;
};
static inline uint32_t db_read(struct ddma_backend *b,unsigned offset) {
 return b->read(b->context,DDMA_BANK+offset);
}
static inline void db_write(struct ddma_backend *b,unsigned offset,uint32_t v) {
 b->write(b->context,DDMA_BANK+offset,v);
}
static inline void db_write64(struct ddma_backend *b,unsigned offset,uint64_t v) {
 db_write(b,offset,v>>32);db_write(b,offset+4,(uint32_t)v);
}
static inline uint64_t db_read64(struct ddma_backend *b,unsigned offset) {
 return ((uint64_t)db_read(b,offset)<<32)|db_read(b,offset+4);
}
/* Suitable ddma_start_fn. Called only with a complete validated padded trace.
 * No DMA abort/reset shortcut on ambiguous admission: latch faulted, let the
 * bounded hardware watchdog drain, require explicit outer restoration.
 */
static inline int ddma_backend_start(void *context,const uint8_t *bytes,size_t length,uint64_t timestamp) {
 struct ddma_backend *b=context;uint64_t now;
 if(!b || !b->read || !b->write || !b->copy || !b->flush || !b->time ||
    !b->ready || !b->delay || b->faulted || !bytes || length!=2048 ||
    !timestamp || timestamp>INT64_MAX || (timestamp&7))return -1;
 if(!b->ready(b->context) || b->time(b->context,&now) || now>INT64_MAX ||
    timestamp<=now || timestamp-now<1000000 || db_read(b,DB_ACTIVE))return -1;
 db_write(b,DB_CLEAR,1);
 if(db_read(b,DB_PENDING) || db_read(b,DB_REJECT))return -1;
 if(b->copy(b->context,DDMA_ARENA,bytes,length))return -1;
 b->flush(b->context,DDMA_ARENA,length); /* must include barrier before MMIO */
 db_write64(b,DB_ADDRESS,DDMA_ARENA);db_write64(b,DB_OFFSET,timestamp);
 db_write(b,DB_BUDGET,16);db_write(b,DB_WATCHDOG,134217728);
 if(db_read64(b,DB_ADDRESS)!=DDMA_ARENA || db_read64(b,DB_OFFSET)!=timestamp ||
    db_read(b,DB_BUDGET)!=16 || db_read(b,DB_WATCHDOG)!=134217728)return -1;
 /* Recheck after memory/cache latency and before irreversible admission. */
 if(!b->ready(b->context) || b->time(b->context,&now) || now>INT64_MAX ||
    timestamp<=now || timestamp-now<1000000)return -1;
 uint32_t accepted=db_read(b,DB_ACCEPTED);
 db_write(b,DB_START,1);
 for(unsigned i=0;i<1000;i++) {
  if(db_read(b,DB_ACCEPTED)==(uint32_t)(accepted+1))return 0;
  if(db_read(b,DB_REJECT)) {b->faulted=1;return -1;}
  b->delay(b->context);
 }
 b->faulted=1;return -1;
}
