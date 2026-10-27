/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "pit_sleep_model.h"
#include "pit_terminal_record.h"
#include "pit_terminal_build.h"
#include "pit_status_compose.h"
struct fake {
    unsigned mode, calls, disabled, reads, valid, terminal;
    uint32_t observations[3], samples[12], receipt[24], msr;
    enum pit_publish_status publication;
    struct pit_attempt receipt_attempt;
    int status;
};
static int observe(void *ctx, uint32_t *out)
{
    struct fake *f=ctx;unsigned n=f->calls++;
    assert(n<3);*out=f->msr;f->observations[n]=*out;
    /* A failing read still writes plausible data: validity must follow return. */
    if((f->mode==0&&n==0)||(f->mode==2&&n==1)||(f->mode==3&&n==2))return -1;
    f->valid|=1u<<n;return 0;
}
static int disable(void *ctx)
{
    struct fake *f=ctx;++f->disabled;
    if(f->mode==1)return -1;
    if(f->mode!=4)f->msr&=~UINT32_C(2);
    return 0;
}
static int read_word(void *ctx,uint32_t address,uint32_t *out)
{
    struct fake *f=ctx;assert(address==UINT32_C(0xffd40044)+(f->reads%4)*16);
    *out=f->reads++;return 0;
}
static int sample_write(void *ctx,uint32_t offset,uint32_t value)
{struct fake *f=ctx;assert(offset<48&&!(offset%4));f->samples[offset/4]=value;return 0;}
static int barrier(void *ctx){(void)ctx;return 0;}
static int receipt_write(void *ctx,uint32_t offset,uint32_t value)
{struct fake *f=ctx;assert(offset<96&&!(offset%4));f->receipt[offset/4]=value;return 0;}
static void emit(const uint32_t *words,unsigned count)
{unsigned i,j;for(i=0;i<count;++i)for(j=0;j<4;++j)putchar((int)((words[i]>>(j*8))&255));}
int main(void)
{
    unsigned mode;
    for(mode=0;mode<6;++mode){
        struct fake f={0};struct pit_status_audit_plan plan={0};
        struct pit_sleep_ops ops={observe,disable,read_word,sample_write,barrier,0};
        const uint32_t image[8]={0x884f7616U,0x32fd6cbeU,0xdcb8d26eU,0xa701518cU,0x58b43df6U,0x52ca1e97U,0xcb61b320U,0xdaaa4eb0U};
        const uint32_t digest[8]={0x309c7563U,0xbea00649U,0xadc9f4c1U,0xc95c2faeU,0xf5b1b669U,0x69aa2086U,0xe4c2c3ceU,0x8bbff9e5U};
        uint32_t header[11];int status;
        f.mode=mode;f.msr=UINT32_C(0x80000106);
        plan.nonce=7;plan.capture_ops=ops;plan.capture_context=&f;
        plan.receipt_write=receipt_write;plan.receipt_barrier=barrier;plan.receipt_context=&f;
        plan.image_digest=image;plan.sample_digest=digest;
        assert(pit_status_compose_model(&plan)==0);
        status=(int)plan.lifecycle_status;
        assert(plan.metadata_status==0&&plan.publication_status==PIT_CALLBACKS_RETURNED_OFFLINE);
        assert(plan.record.status==(uint32_t)status);
        assert(pit_status_compose_model(&plan)==-1);
        assert(status==(mode==5?PIT_SLEEP_CAPTURE_COMPLETE:PIT_SLEEP_IRQ_UNPROVEN));

        if(mode<3||mode==4)assert(!f.reads&&!f.samples[0]);else assert(f.reads==8&&f.samples[0]==1);
        header[0]=0x504d4f31;header[1]=1;header[2]=mode;header[3]=f.valid;
        header[4]=f.calls;header[5]=f.disabled;header[6]=f.reads;
        header[7]=(uint32_t)status;header[8]=f.observations[0];header[9]=f.observations[1];header[10]=f.observations[2];
        emit(header,11);emit(f.samples,12);emit(f.receipt,24);
    }
    return 0;
}
