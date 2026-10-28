/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include "pit_ro_adapter.h"
struct fake {struct pit_ro_adapter *adapter;unsigned calls;int fail;};
static int raw_read(void *ctx,uint32_t address,uint32_t *out)
{
    struct fake *f=ctx;uint32_t nested=123;
    unsigned n=f->calls++;
    assert(address==UINT32_C(0xffd40044)+(n%4)*16);
    assert(pit_ro_read(f->adapter,address,&nested)==-1&&nested==123);
    *out=100+n;
    return (int)n==f->fail?9:0;
}
int main(void)
{
    int fail;
    for(fail=-1;fail<8;++fail){
        struct pit_ro_adapter adapter={0};struct fake f={&adapter,0,fail};
        struct pit_attempt attempt={0};struct pit_record record={0};
        enum pit_status status;uint32_t value=123;
        assert(pit_ro_prepare(&adapter,raw_read,&f)==0);
        assert(pit_ro_prepare(&adapter,raw_read,&f)==-1);
        status=pit_collect(&attempt,&record,7,pit_ro_read,&adapter);
        assert(status==(fail<0?PIT_COMPLETE_OFFLINE:PIT_INCOMPLETE));
        assert(f.calls==(fail<0?8u:(unsigned)fail+1));
        assert(record.complete==(fail<0?1u:0u));
        if(fail<0){unsigned i;for(i=0;i<8;++i)assert(record.values[i]==100+i);}
        assert(pit_ro_read(&adapter,UINT32_C(0xffd40044),&value)==-1&&value==123);
        assert(f.calls==(fail<0?8u:(unsigned)fail+1));
        assert(pit_ro_prepare(&adapter,raw_read,&f)==-1);
    }
    {
        uint32_t forbidden[]={0xffd40010,0xffd40040,0xffd40048,0xffd40054,0xff413030,0xffd40045};
        unsigned i;
        for(i=0;i<sizeof forbidden/sizeof forbidden[0];++i){
            struct pit_ro_adapter adapter={0};struct fake f={&adapter,0,-1};uint32_t value=123;
            assert(pit_ro_prepare(&adapter,raw_read,&f)==0);
            assert(pit_ro_read(&adapter,forbidden[i],&value)==-1&&value==123&&!f.calls);
            assert(pit_ro_read(&adapter,0xffd40044,&value)==-1&&!f.calls);
        }
    }
    {
        struct pit_ro_adapter adapter={0};struct fake f={&adapter,0,0};uint32_t value=123;
        assert(pit_ro_read(&adapter,0xffd40044,&value)==-1&&!f.calls);
        assert(pit_ro_prepare(&adapter,0,&f)==-1);
        assert(pit_ro_prepare(&adapter,raw_read,&f)==0);
        assert(pit_ro_read(&adapter,0xffd40044,&value)==-1&&value==123&&f.calls==1);
        /* A transport-written failure value never escapes the adapter. */
    }
    return 0;
}
