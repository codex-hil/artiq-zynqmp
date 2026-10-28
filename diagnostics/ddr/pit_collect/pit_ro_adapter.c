/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include "pit_ro_adapter.h"
int pit_ro_prepare(struct pit_ro_adapter *adapter, pit_read_fn transport, void *context)
{
    if(!adapter||!transport||adapter->armed||adapter->attempted||adapter->failed||adapter->busy)
        return -1;
    adapter->transport=transport;adapter->context=context;adapter->armed=1;
    return 0;
}
int pit_ro_read(void *ctx, uint32_t address, uint32_t *out)
{
    struct pit_ro_adapter *adapter=ctx;
    uint32_t value=0, expected;
    int result;
    if(!adapter||!adapter->armed||!adapter->transport||adapter->busy||adapter->failed)
        return -1;
    if(!out||adapter->attempted>=8){adapter->failed=1;return -1;}
    expected=UINT32_C(0xffd40044)+(adapter->attempted%4)*16;
    if(address!=expected){adapter->failed=1;return -1;}
    adapter->busy=1;
    ++adapter->attempted; /* Consume before transport; no replay after error. */
    result=adapter->transport(adapter->context,address,&value);
    adapter->busy=0;
    if(result){adapter->failed=1;return -1;}
    *out=value;
    return 0;
}
