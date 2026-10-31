/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_sample_sha256.h"
#include <stddef.h>
static uint32_t ror(uint32_t x,unsigned n){return (x>>n)|(x<<(32-n));}
static uint32_t swap(uint32_t x){return (x>>24)|((x>>8)&0xff00u)|((x<<8)&0xff0000u)|(x<<24);}
static const uint32_t k[64]={
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
__attribute__((noinline,used)) int pit_sample_sha256(const uint32_t in[12],uint64_t nonce,uint32_t out[8])
{
    volatile uint32_t w[64];
    uint32_t a=0x6a09e667,b=0xbb67ae85,c=0x3c6ef372,d=0xa54ff53a;
    uint32_t e=0x510e527f,f=0x9b05688c,g=0x1f83d9ab,h=0x5be0cd19;
    unsigned i;
    if(!in||!out||!nonce||((uintptr_t)in&3u)||((uintptr_t)out&3u))return -1;
    if((uintptr_t)in<=(uintptr_t)out ? (uintptr_t)out-(uintptr_t)in<48u : (uintptr_t)in-(uintptr_t)out<32u)return -1;
    /* Snapshot each input word exactly once before validation or output. */
    for(i=0;i<12;i++)w[i]=((const volatile uint32_t *)in)[i];
    if(w[0]!=1||w[1]!=1||w[2]!=(uint32_t)nonce||w[3]!=(uint32_t)(nonce>>32))return -1;
    for(i=0;i<12;i++)w[i]=swap(w[i]);
    w[12]=0x80000000u;w[13]=0;w[14]=0;w[15]=384;
    for(i=16;i<64;i++){
        uint32_t x=w[i-15],y=w[i-2];
        w[i]=w[i-16]+(ror(x,7)^ror(x,18)^(x>>3))+w[i-7]+(ror(y,17)^ror(y,19)^(y>>10));
    }
    for(i=0;i<64;i++){
        uint32_t t1=h+(ror(e,6)^ror(e,11)^ror(e,25))+((e&f)^((~e)&g))+k[i]+w[i];
        uint32_t t2=(ror(a,2)^ror(a,13)^ror(a,22))+((a&b)^(a&c)^(b&c));
        h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
    }
    ((volatile uint32_t *)out)[0]=swap(a+0x6a09e667u);
    ((volatile uint32_t *)out)[1]=swap(b+0xbb67ae85u);
    ((volatile uint32_t *)out)[2]=swap(c+0x3c6ef372u);
    ((volatile uint32_t *)out)[3]=swap(d+0xa54ff53au);
    ((volatile uint32_t *)out)[4]=swap(e+0x510e527fu);
    ((volatile uint32_t *)out)[5]=swap(f+0x9b05688cu);
    ((volatile uint32_t *)out)[6]=swap(g+0x1f83d9abu);
    ((volatile uint32_t *)out)[7]=swap(h+0x5be0cd19u);
    return 0;
}
