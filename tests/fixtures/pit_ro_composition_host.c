/* SPDX-License-Identifier: LGPL-3.0-or-later */
#define main earlier_fixture_main
#include "pit_status_compose_host.c"
#undef main
#include "pit_ro_adapter.h"
struct chain {
    struct fake f;
    struct pit_ro_adapter ro;
    struct pit_status_audit_plan plan;
    unsigned raw_calls, sample_writes, receipt_writes;
    int fail, bad_address;
};
static int raw(void *ctx,uint32_t address,uint32_t *out)
{
    struct chain *c=ctx;unsigned n=c->raw_calls++;uint32_t nested=123;
    assert(address==UINT32_C(0xffd40044)+(n%4)*16);
    assert(pit_ro_read(&c->ro,address,&nested)==-1&&nested==123);
    *out=n;
    return (int)n==c->fail?-1:0;
}
static int chain_msr(void *ctx,uint32_t *out){struct chain *c=ctx;return observe(&c->f,out);}
static int chain_disable(void *ctx){struct chain *c=ctx;return disable(&c->f);}
static int guarded_read(void *ctx,uint32_t address,uint32_t *out)
{struct chain *c=ctx;return pit_ro_read(&c->ro,c->bad_address?UINT32_C(0xffd40010):address,out);}
static int chain_write(void *ctx,uint32_t offset,uint32_t value)
{struct chain *c=ctx;++c->sample_writes;return sample_write(&c->f,offset,value);}
static int chain_barrier(void *ctx){struct chain *c=ctx;return barrier(&c->f);}
static int chain_receipt(void *ctx,uint32_t offset,uint32_t value)
{struct chain *c=ctx;++c->receipt_writes;return receipt_write(&c->f,offset,value);}
int main(void)
{
    const uint32_t image[8]={0x884f7616U,0x32fd6cbeU,0xdcb8d26eU,0xa701518cU,0x58b43df6U,0x52ca1e97U,0xcb61b320U,0xdaaa4eb0U};
    const uint32_t digest[8]={0x309c7563U,0xbea00649U,0xadc9f4c1U,0xc95c2faeU,0xf5b1b669U,0x69aa2086U,0xe4c2c3ceU,0x8bbff9e5U};
    int scenario;
    for(scenario=-1;scenario<10;++scenario){
        struct chain c={0};uint32_t sentinel=123;unsigned saved;
        c.fail=scenario<8?scenario:-1;c.f.mode=5;c.f.msr=0x80000106;
        assert(pit_ro_prepare(&c.ro,raw,&c)==0);
        if(scenario==8)c.bad_address=1;
        if(scenario==9){
            /* Exhaust fake transport before the model to test stale/reused budget. */
            unsigned i;for(i=0;i<8;++i)assert(pit_ro_read(&c.ro,0xffd40044+(i%4)*16,&sentinel)==0);
        }
        c.plan.nonce=7;c.plan.capture_context=&c;c.plan.receipt_context=&c;
        c.plan.capture_ops=(struct pit_sleep_ops){chain_msr,chain_disable,guarded_read,chain_write,chain_barrier,0};
        c.plan.receipt_write=chain_receipt;c.plan.receipt_barrier=chain_barrier;
        c.plan.image_digest=image;c.plan.sample_digest=digest;
        assert(pit_status_compose_model(&c.plan)==0);
        assert(c.plan.lifecycle_status==(scenario<0?PIT_SLEEP_CAPTURE_COMPLETE:PIT_SLEEP_READ_FAILED));
        assert(c.plan.metadata_status==0&&c.plan.record.status==c.plan.lifecycle_status);
        assert(c.plan.publication_status==PIT_CALLBACKS_RETURNED_OFFLINE&&c.receipt_writes==25);
        assert(c.sample_writes==(scenario<0?13u:0u));
        assert(c.raw_calls==(scenario<0||scenario==9?8u:(scenario==8?0u:(unsigned)scenario+1)));
        saved=c.raw_calls;sentinel=123;
        assert(pit_ro_read(&c.ro,0xffd40044,&sentinel)==-1&&sentinel==123&&c.raw_calls==saved);
        assert(pit_ro_prepare(&c.ro,raw,&c)==-1);
        assert(pit_status_compose_model(&c.plan)==-1&&c.raw_calls==saved);
        emit(c.f.samples,12);emit(c.f.receipt,24);
    }
    return 0;
}
