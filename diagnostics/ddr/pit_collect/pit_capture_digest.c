/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_capture_digest.h"
#include "pit_sample_sha256.h"
enum pit_digest_status pit_capture_digest(struct pit_digest_attempt *state,uint64_t nonce,
    pit_read_fn read,pit_write_fn write,pit_barrier_fn barrier,void *ctx)
{
    struct pit_attempt collection={0},publication={0};
    union { struct pit_record record; uint32_t words[12]; } snapshot;
    uint32_t digest[8];
    unsigned i;
    _Static_assert(sizeof(snapshot)==48,"canonical sample size");
    if(!state||!nonce||!read||!write||!barrier||state->consumed||state->digest_valid)
        return PIT_DIGEST_REJECTED;
    for(i=0;i<8;i++)if(state->digest_le[i])return PIT_DIGEST_REJECTED;
    state->consumed=1;
    for(i=0;i<12;i++)((volatile uint32_t *)snapshot.words)[i]=0;
    if(pit_collect(&collection,&snapshot.record,nonce,read,ctx)!=PIT_COMPLETE_OFFLINE)
        return PIT_DIGEST_READ_FAILED;
    if(pit_sample_sha256(snapshot.words,nonce,digest))return PIT_DIGEST_HASH_FAILED;
    for(i=0;i<8;i++)((volatile uint32_t *)state->digest_le)[i]=digest[i];
    state->digest_valid=1;
    if(pit_publish(&publication,&snapshot.record,nonce,write,barrier,ctx)!=PIT_CALLBACKS_RETURNED_OFFLINE)
        return PIT_DIGEST_PUBLICATION_UNKNOWN;
    return PIT_DIGEST_CALLBACKS_RETURNED_OFFLINE;
}
