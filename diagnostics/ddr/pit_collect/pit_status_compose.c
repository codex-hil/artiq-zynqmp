/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_status_compose.h"
struct forwarding {
    struct pit_sleep_ops ops;
    void *context;
    struct pit_terminal_observations observations;
    unsigned msr_calls, reads;
    int read_failed, publish_failed;
};
static int observe(void *ctx, uint32_t *out)
{
    struct forwarding *f=ctx;
    uint32_t value=0;
    unsigned n=f->msr_calls++;
    int result;
    if(n>=3)return -1;
    result=f->ops.msr(f->context,&value);
    f->observations.called_mask|=1u<<n;
    f->observations.returns[n]=result;
    f->observations.msr[n]=value;
    *out=value;
    return result;
}
static int disable(void *ctx)
{struct forwarding *f=ctx;return f->ops.disable(f->context);}
static int read_word(void *ctx,uint32_t address,uint32_t *out)
{
    struct forwarding *f=ctx;int result=f->ops.read(f->context,address,out);
    ++f->reads;if(result)f->read_failed=1;return result;
}
static int write_word(void *ctx,uint32_t offset,uint32_t value)
{
    struct forwarding *f=ctx;int result=f->ops.write(f->context,offset,value);
    if(result) f->publish_failed=1;
    return result;
}
static int barrier(void *ctx)
{
    struct forwarding *f=ctx;int result=f->ops.barrier(f->context);
    if(result) f->publish_failed=1;
    return result;
}
static void defer(void *ctx,int result){(void)ctx;(void)result;}
int pit_status_compose_model(struct pit_status_audit_plan *plan)
{
    struct forwarding f;
    struct pit_sleep_ops local={observe,disable,read_word,write_word,barrier,defer};
    unsigned i;
    const uint32_t *sample;
    if(!plan||plan->consumed||plan->capture.consumed||plan->publication.consumed||plan->record.commit||!plan->nonce||!plan->capture_ops.msr||
       !plan->capture_ops.disable||!plan->capture_ops.read||!plan->capture_ops.write||
       !plan->capture_ops.barrier||!plan->receipt_write||!plan->receipt_barrier||!plan->image_digest)
        return -1;
    plan->consumed=1;
    f.ops.msr=plan->capture_ops.msr;f.ops.disable=plan->capture_ops.disable;
    f.ops.read=plan->capture_ops.read;f.ops.write=plan->capture_ops.write;
    f.ops.barrier=plan->capture_ops.barrier;f.ops.terminal=defer;
    f.context=plan->capture_context;f.observations.called_mask=0;
    f.msr_calls=0;f.reads=0;f.read_failed=0;f.publish_failed=0;
    for(i=0;i<3;++i){
        ((volatile int32_t *)f.observations.returns)[i]=-1;
        ((volatile uint32_t *)f.observations.msr)[i]=0;
    }
    plan->lifecycle_status=(uint32_t)pit_sleep_model(&plan->capture,plan->nonce,&local,&f);
    f.observations.sample_outcome=f.read_failed?2u:(f.publish_failed?3u:(f.reads==8?4u:1u));
    sample=f.observations.sample_outcome>=3?plan->sample_digest:0;
    plan->metadata_status=pit_terminal_build(&plan->record,&f.observations,plan->nonce,plan->image_digest,sample);
    if(!plan->metadata_status && plan->record.status != plan->lifecycle_status)
        plan->metadata_status=-1;
    plan->publication_status=PIT_PUBLISH_REJECTED;
    if(!plan->metadata_status)
        plan->publication_status=(uint32_t)pit_terminal_publish(&plan->publication,&plan->record,
            plan->nonce,plan->receipt_write,plan->receipt_barrier,plan->receipt_context);
    return 0; /* Model finished, not hardware/sleep success. */
}
