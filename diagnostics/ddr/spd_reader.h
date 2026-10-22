/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef GENESYS_SPD_READER_H
#define GENESYS_SPD_READER_H
#include <stdint.h>
#include <string.h>
/* Transaction orchestration only; adapter must use nonblocking AMD XIicPs.
 * No controller implementation, retries, mux access or EEPROM data programming.
 * Caller must prove exclusive I2C1 ownership and known lower-page baseline.
 */
enum spd_op { SPD_LOWER_PAGE, SPD_OFFSET, SPD_READ };
enum spd_result { SPD_BUSY, SPD_PASS, SPD_IO_ERROR, SPD_DEADLINE,
                  SPD_MISMATCH, SPD_NOT_ADMITTED };
struct spd_transport {
    void *ctx;
    int (*begin)(void *, enum spd_op, unsigned, uint8_t *, unsigned);
    int (*poll)(void *); /* 0=pending, 1=complete+bus idle, negative=error */
    int (*idle)(void *); /* 1=bus idle AND no active driver transfer/callback;
                           * 0=busy, negative=unknown/error */
};
struct spd_reader {
    struct spd_transport io;
    uint8_t bytes[2][128], zero;
    unsigned step, polls;
    uint64_t deadline, last_now;
    enum spd_result result;
    int active, cleanup, page_restored, stopped;
};
static inline int spd_start_step(struct spd_reader *r, uint64_t now) {
    enum spd_op op;
    unsigned address, count=1;
    uint8_t *data=&r->zero;
    if (r->step==0 || r->cleanup) {op=SPD_LOWER_PAGE; address=0x36;}
    else if (r->step==1 || r->step==3) {op=SPD_OFFSET; address=0x51;}
    else {op=SPD_READ; address=0x51;count=128;data=r->bytes[r->step==2?0:1];}
    r->deadline=now+100000; r->polls=0;
    if (r->deadline < now) return -1;
    r->active=1;
    return r->io.begin(r->io.ctx,op,address,data,count);
}
static inline void spd_finish_failure(struct spd_reader *r, enum spd_result why) {
    r->result=why;
    r->active=0;
    /* No cleanup transaction on a busy/unknown bus; no bus-clear workaround. */
    if (r->cleanup || r->io.idle(r->io.ctx)!=1) {r->stopped=1;return;}
    r->cleanup=1;
    if (spd_start_step(r,r->last_now)!=0) {r->active=0;r->stopped=1;}
}
static inline void spd_reader_init(struct spd_reader *r, struct spd_transport io,
                                   uint64_t now, int exclusive_lower_page_known) {
    memset(r,0,sizeof(*r));r->io=io;r->last_now=now;r->result=SPD_BUSY;
    if (!exclusive_lower_page_known || !io.begin || !io.poll || !io.idle) {
        r->result=SPD_NOT_ADMITTED;r->stopped=1;return;
    }
    if (io.idle(io.ctx)!=1) {r->result=SPD_NOT_ADMITTED;r->stopped=1;return;}
    if (spd_start_step(r,now)!=0) spd_finish_failure(r,SPD_IO_ERROR);
}
static inline void spd_reader_tick(struct spd_reader *r, uint64_t now) {
    int status;
    if (r->stopped) return;
    if (now<r->last_now || now>=r->deadline || ++r->polls>10000) {
        r->last_now=now;spd_finish_failure(r,SPD_DEADLINE);return;
    }
    r->last_now=now;status=r->io.poll(r->io.ctx);
    if (status==0) return;
    if (status!=1) {spd_finish_failure(r,SPD_IO_ERROR);return;}
    r->active=0;
    if (r->io.idle(r->io.ctx)!=1) {spd_finish_failure(r,SPD_IO_ERROR);return;}
    if (r->cleanup) {r->page_restored=1;r->stopped=1;return;}
    if (++r->step==5) {
        r->result=memcmp(r->bytes[0],r->bytes[1],128)?SPD_MISMATCH:SPD_PASS;
        r->cleanup=1;
    }
    if (spd_start_step(r,now)!=0) spd_finish_failure(r,SPD_IO_ERROR);
}
#endif
