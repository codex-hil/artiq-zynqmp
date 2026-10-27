/* SPDX-License-Identifier: LGPL-3.0-or-later */
/* Reuse the actual fake-backend functions; their original main is not run. */
#define main original_fixture_main
#include "pit_status_compose_host.c"
#undef main
#include <string.h>
struct faults {
    struct fake f;
    struct pit_status_audit_plan plan;
    unsigned callbacks, receipt_calls;
    int cut, after;
};
static void reenter(struct faults *c)
{ assert(pit_status_compose_model(&c->plan)==-1); }
static int checked_msr(void *ctx,uint32_t *value)
{struct faults *c=ctx;reenter(c);++c->callbacks;return observe(&c->f,value);}
static int checked_disable(void *ctx)
{struct faults *c=ctx;reenter(c);++c->callbacks;return disable(&c->f);}
static int checked_read(void *ctx,uint32_t address,uint32_t *value)
{struct faults *c=ctx;reenter(c);++c->callbacks;return read_word(&c->f,address,value);}
static int checked_write(void *ctx,uint32_t offset,uint32_t value)
{struct faults *c=ctx;reenter(c);++c->callbacks;return sample_write(&c->f,offset,value);}
static int checked_barrier(void *ctx)
{struct faults *c=ctx;reenter(c);++c->callbacks;return barrier(&c->f);}
static int receipt_event_checked(struct faults *c,int is_barrier,uint32_t offset,uint32_t value)
{
    unsigned n=c->receipt_calls++;
    reenter(c);++c->callbacks;
    assert(is_barrier==(n==1||n==25));
    if((int)n==c->cut&&!c->after)return -1;
    if(!is_barrier)assert(receipt_write(&c->f,offset,value)==0);
    return (int)n==c->cut&&c->after?-1:0;
}
static int checked_receipt_write(void *ctx,uint32_t offset,uint32_t value)
{return receipt_event_checked(ctx,0,offset,value);}
static int checked_receipt_barrier(void *ctx)
{return receipt_event_checked(ctx,1,0,0);}
static const uint32_t image_digest[8]={1},sample_digest[8]={2},zero_digest[8]={0};
static void setup(struct faults *c)
{
    memset(c,0,sizeof *c);c->f.mode=5;c->f.msr=0x80000106;c->cut=-1;
    c->plan.nonce=7;
    c->plan.capture_ops=(struct pit_sleep_ops){checked_msr,checked_disable,checked_read,checked_write,checked_barrier,0};
    c->plan.capture_context=c;c->plan.receipt_context=c;
    c->plan.receipt_write=checked_receipt_write;c->plan.receipt_barrier=checked_receipt_barrier;
    c->plan.image_digest=image_digest;c->plan.sample_digest=sample_digest;
}
int main(void)
{
    struct faults c;
    int cut,after,which;
    for(after=0;after<2;++after)for(cut=-1;cut<27;++cut){
        unsigned count;
        setup(&c);c.cut=cut;c.after=after;
        assert(pit_status_compose_model(&c.plan)==0);
        assert(c.plan.lifecycle_status==PIT_SLEEP_CAPTURE_COMPLETE&&c.plan.metadata_status==0);
        assert(c.plan.publication_status==(cut<0?PIT_CALLBACKS_RETURNED_OFFLINE:PIT_VISIBILITY_UNKNOWN));
        assert(c.receipt_calls==(cut<0?27u:(unsigned)cut+1));
        assert(c.plan.capture.consumed&&c.plan.publication.consumed&&c.plan.consumed);
        assert(c.f.samples[0]==1);
        assert(c.f.receipt[0]==(cut<0||(cut==26&&after)?1u:0u));
        count=c.callbacks;assert(pit_status_compose_model(&c.plan)==-1);assert(c.callbacks==count);
    }
    for(which=0;which<3;++which){
        setup(&c);
        if(which==0)c.plan.image_digest=zero_digest;
        if(which==1)c.plan.sample_digest=0;
        if(which==2)c.plan.sample_digest=zero_digest;
        assert(pit_status_compose_model(&c.plan)==0);
        assert(c.plan.lifecycle_status==PIT_SLEEP_CAPTURE_COMPLETE&&c.plan.metadata_status==-1);
        assert(c.plan.publication_status==PIT_PUBLISH_REJECTED&&!c.receipt_calls&&!c.plan.publication.consumed);
        assert(c.f.samples[0]==1); /* Metadata error does not erase successful samples. */
    }
    for(which=0;which<7;++which){
        struct pit_status_audit_plan before;
        setup(&c);
        if(which==0)c.plan.consumed=1;
        if(which==1)c.plan.capture.consumed=1;
        if(which==2)c.plan.publication.consumed=1;
        if(which==3)c.plan.record.commit=1;
        if(which==4)c.plan.nonce=0;
        if(which==5)c.plan.capture_ops.msr=0;
        if(which==6)c.plan.image_digest=0;
        before=c.plan;
        assert(pit_status_compose_model(&c.plan)==-1&&!c.callbacks);
        assert(!memcmp(&before,&c.plan,sizeof before));
    }
    assert(pit_status_compose_model(0)==-1);
    return 0;
}
