/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_digest_compose.h"
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
    struct forwarding *f=ctx;
    int result=f->ops.read(f->context,address,out);
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
int pit_digest_compose(struct pit_digest_plan *plan)
{
 struct forwarding f;
 struct pit_sleep_ops local={observe,disable,read_word,write_word,barrier,defer};
 struct pit_digest_attempt digest;
 struct pit_attempt publication={0};
 uint32_t image[8];
 uint64_t nonce;
 pit_write_fn receipt_write;
 pit_barrier_fn receipt_barrier;
 void *receipt_context;
 unsigned i;
 if(!plan||plan->consumed||!plan->nonce||!plan->image_digest||!plan->ops.msr||
    !plan->ops.disable||!plan->ops.read||!plan->ops.write||!plan->ops.barrier||
    !plan->receipt_write||!plan->receipt_barrier)return -1;
 for(i=0;i<96;i++)if(((const volatile unsigned char *)&plan->record)[i])return -1;
 for(i=0;i<8;i++)((volatile uint32_t *)image)[i]=plan->image_digest[i];
 nonce=plan->nonce;receipt_write=plan->receipt_write;receipt_barrier=plan->receipt_barrier;
 receipt_context=plan->receipt_context;
 f.ops=plan->ops;f.context=plan->capture_context;
 f.msr_calls=0;f.reads=0;f.read_failed=0;f.publish_failed=0;
 f.observations.called_mask=0;
 for(i=0;i<3;i++){
  ((volatile int32_t *)f.observations.returns)[i]=-1;
  ((volatile uint32_t *)f.observations.msr)[i]=0;
 }
 digest.consumed=0;digest.digest_valid=0;
 for(i=0;i<8;i++)((volatile uint32_t *)digest.digest_le)[i]=0;
 plan->consumed=1;
 plan->metadata_status=-1;plan->publication_status=PIT_PUBLISH_REJECTED;
 plan->lifecycle_status=(uint32_t)pit_digest_sleep(&digest,nonce,&local,&f);
 /* No valid digest after eight successful reads means hash failure, including
  * failure hidden by final IRQ-unproven override. Never synthesize v1 receipt. */
 if(plan->lifecycle_status==PIT_DS_HASH_FAILED||(!f.read_failed&&f.reads==8&&!digest.digest_valid))return 0;
 f.observations.sample_outcome=f.read_failed?2u:(digest.digest_valid?(f.publish_failed?3u:4u):1u);
 plan->metadata_status=pit_digest_terminal(&plan->record,&digest,
  (enum pit_digest_sleep_status)plan->lifecycle_status,&f.observations,nonce,image);
 if(!plan->metadata_status)
  plan->publication_status=(uint32_t)pit_terminal_publish(&publication,&plan->record,
   nonce,receipt_write,receipt_barrier,receipt_context);
 return 0; /* Model completion only; terminal receipt is intent, not sleep. */
}
