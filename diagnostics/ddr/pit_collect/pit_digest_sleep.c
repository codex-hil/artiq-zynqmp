/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_digest_sleep.h"
enum pit_digest_sleep_status pit_digest_sleep(struct pit_digest_attempt *state,uint64_t nonce,
 const struct pit_sleep_ops *ops,void *ctx)
{
 uint32_t before=0,after=0,final=0;
 struct pit_sleep_ops local;
 enum pit_digest_sleep_status result=PIT_DS_IRQ_UNPROVEN;
 enum pit_digest_status capture;
 unsigned i;
 if(!state||!nonce||!ops||!ops->msr||!ops->disable||!ops->read||!ops->write||
    !ops->barrier||!ops->terminal||state->consumed||state->digest_valid)return PIT_DS_REJECTED;
 for(i=0;i<8;i++)if(state->digest_le[i])return PIT_DS_REJECTED;
 local=*ops;
 /* Reserve before callbacks so reentry cannot consume a second attempt.
  * Private capture state is never exposed to callbacks via this API. */
 state->consumed=1;
 {
  struct pit_digest_attempt private_state;
  private_state.consumed=0;private_state.digest_valid=0;
  for(i=0;i<8;i++)((volatile uint32_t *)private_state.digest_le)[i]=0;
  if(local.msr(ctx,&before)||local.disable(ctx)||local.msr(ctx,&after)||
     after!=(before&~UINT32_C(2)))goto terminal;
  capture=pit_capture_digest(&private_state,nonce,local.read,local.write,local.barrier,ctx);
  if(private_state.digest_valid){
   for(i=0;i<8;i++)((volatile uint32_t *)state->digest_le)[i]=private_state.digest_le[i];
   state->digest_valid=1;
  }
  switch(capture){
  case PIT_DIGEST_CALLBACKS_RETURNED_OFFLINE:result=PIT_DS_CALLBACKS_RETURNED;break;
  case PIT_DIGEST_PUBLICATION_UNKNOWN:result=PIT_DS_PUBLICATION_UNKNOWN;break;
  case PIT_DIGEST_HASH_FAILED:result=PIT_DS_HASH_FAILED;break;
  default:result=PIT_DS_READ_FAILED;break;
  }
 }
 /* Hash, sample publication and digest copy all precede final observation.
  * A digest can remain valid while final IRQ policy is unproven. */
 if(local.msr(ctx,&final)||final!=after)result=PIT_DS_IRQ_UNPROVEN;
terminal:
 local.terminal(ctx,(int)result);
 return result; /* Returning model only, never sleep residency proof. */
}
