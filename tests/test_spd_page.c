/* SPDX-License-Identifier: LGPL-3.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "../diagnostics/ddr/spd_page.h"
static struct spd_page_reply zero(void) {
 return (struct spd_page_reply){.address=0x36,.requested=1,.received=1,
 .raw_irq=XIICPS_IXR_COMP_MASK,.events=XIICPS_EVENT_COMPLETE_RECV,
 .exclusive_route_proven=1,.independent_spd_identity_proven=1,.bus_idle=1,.fifo_empty=1};
}
int main(void) {
 struct spd_page_reply a=zero(),b=a;
 assert(spd_classify_page(a)==SPD_PAGE_ZERO);
 a.raw_irq|=XIICPS_IXR_DATA_MASK;assert(spd_classify_page(a)==SPD_PAGE_ZERO);
 b.received=0;b.raw_irq=XIICPS_IXR_NACK_MASK;b.events=XIICPS_EVENT_NACK|XIICPS_EVENT_ERROR;
 assert(spd_classify_page(b)==SPD_PAGE_ONE);
 for(unsigned i=0;i<11;i++) {
  struct spd_page_reply r=b;
  if(i==0)r.address=0x51;
  if(i==1)r.requested=128;
  if(i==2)r.exclusive_route_proven=0;
  if(i==3)r.independent_spd_identity_proven=0;
  if(i==4)r.bus_idle=0;
  if(i==5)r.fifo_empty=0;
  if(i==6)r.timed_out=1;
  if(i==7)r.raw_irq|=XIICPS_IXR_ARB_LOST_MASK;
  if(i==8)r.events|=XIICPS_EVENT_COMPLETE_RECV;
  if(i==9)r.received=1;
  if(i==10)r.events=XIICPS_EVENT_ERROR;
  assert(spd_classify_page(r)==SPD_PAGE_UNKNOWN);
 }
 assert(spd_page_select_address(SPD_PAGE_ZERO)==0x36);
 assert(spd_page_select_address(SPD_PAGE_ONE)==0x37);
 assert(spd_page_select_address(SPD_PAGE_UNKNOWN)==-1);
 assert(spd_page_restore_confirmed(SPD_PAGE_ZERO,a));
 assert(spd_page_restore_confirmed(SPD_PAGE_ONE,b));
 assert(!spd_page_restore_confirmed(SPD_PAGE_ZERO,b));
 assert(!spd_page_restore_confirmed(SPD_PAGE_ONE,a));
 assert(!spd_page_restore_confirmed(SPD_PAGE_UNKNOWN,b));
 puts("SPD page pure classification/admission/restoration controls PASS");
}
