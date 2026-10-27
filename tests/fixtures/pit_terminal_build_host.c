/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <string.h>
#include "pit_terminal_build.h"
int main(void)
{
    struct pit_terminal_observations obs={7,{0,0,0},{0x106,0x104,0x104},4};
    uint32_t image[8]={1},sample[8]={2},zero[8]={0};
    struct pit_terminal_record out,original;
    unsigned i;
    assert(pit_terminal_build(&out,&obs,UINT64_C(0x123456789abcdef0),image,sample)==0);
    assert(out.status==4&&out.nonce==UINT64_C(0x123456789abcdef0));
    obs.returns[2]=-1;obs.msr[2]=0x104;
    assert(pit_terminal_build(&out,&obs,7,image,sample)==0);
    assert(out.status==1&&out.final_msr==0); /* Failed output discarded. */
    obs.returns[2]=0;obs.msr[2]=0x106;
    assert(pit_terminal_build(&out,&obs,7,image,sample)==0&&out.status==1);
    obs.msr[2]=0x104;
    memset(&original,0x5a,sizeof original);
    for(i=0;i<8;++i){
        struct pit_terminal_observations bad=obs;
        const uint32_t *im=image,*sa=sample;
        uint64_t nonce=7;
        if(i==0)bad.called_mask=2;
        if(i==1)bad.sample_outcome=0;
        if(i==2)bad.sample_outcome=5;
        if(i==3)bad.returns[0]=-1;
        if(i==4)bad.sample_outcome=2;
        if(i==5)im=zero;
        if(i==6)sa=zero;
        if(i==7)nonce=0;
        out=original;
        assert(pit_terminal_build(&out,&bad,nonce,im,sa)==-1);
        assert(!memcmp(&out,&original,sizeof out));
    }
    assert(pit_terminal_build(0,&obs,7,image,sample)==-1);
    assert(pit_terminal_build(&out,0,7,image,sample)==-1);
    assert(pit_terminal_build(&out,&obs,7,0,sample)==-1);
    return 0;
}
