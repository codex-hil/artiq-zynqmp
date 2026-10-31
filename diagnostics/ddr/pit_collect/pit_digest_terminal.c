/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_digest_terminal.h"
int pit_digest_terminal(struct pit_terminal_record *out,const struct pit_digest_attempt *state,
 enum pit_digest_sleep_status result,const struct pit_terminal_observations *obs,
 uint64_t nonce,const uint32_t image[8])
{
 union { struct pit_terminal_record record; uint32_t words[24]; } candidate;
 const uint32_t *sample=0;
 unsigned i;
 uint32_t nonzero=0;
 _Static_assert(sizeof(candidate)==96,"terminal word copy");
 if(!out||!state||!obs||!nonce||!image||state->consumed!=1||state->digest_valid>1||
    result<PIT_DS_IRQ_UNPROVEN||result>PIT_DS_CALLBACKS_RETURNED)return -1;
 /* No silent mapping of explicit HASH_FAILED (5), REJECTED (0) or unknown values. */
 for(i=0;i<96;i++)if(((const volatile unsigned char *)out)[i])return -1;
 for(i=0;i<8;i++)nonzero|=state->digest_le[i];
 if(state->digest_valid){
  if(!nonzero||(obs->sample_outcome!=3&&obs->sample_outcome!=4))return -1;
  sample=state->digest_le;
 }else if(nonzero||(obs->sample_outcome!=1&&obs->sample_outcome!=2))return -1;
 for(i=0;i<24;i++)((volatile uint32_t *)candidate.words)[i]=0;
 if(pit_terminal_build(&candidate.record,obs,nonce,image,sample)||candidate.record.status!=(uint32_t)result)
  return -1;
 /* Private result only: no external-reader publication/atomicity claim. */
 out->commit=candidate.record.commit;out->magic=candidate.record.magic;
 out->version=candidate.record.version;out->status=candidate.record.status;
 out->nonce=candidate.record.nonce;out->checked_msr=candidate.record.checked_msr;
 out->final_msr=candidate.record.final_msr;
 for(i=0;i<8;i++){
  ((volatile uint32_t *)out->image_sha256_le)[i]=candidate.record.image_sha256_le[i];
  ((volatile uint32_t *)out->sample_sha256_le)[i]=candidate.record.sample_sha256_le[i];
 }
 return 0;
}
