/* SPDX-License-Identifier: LGPL-3.0-or-later */
#ifndef GENESYS_SPD_SESSION_H
#define GENESYS_SPD_SESSION_H
#include "spd_page_transfer.h"
enum spd_session_result { SPD_SESSION_BUSY, SPD_SESSION_READS_RESTORED,
 SPD_SESSION_FAILED_RESTORED, SPD_SESSION_OUTER_RESTORE_REQUIRED, SPD_SESSION_NOT_ADMITTED };
struct spd_session {
 XIicPs *dev;struct spd_amd_snapshot saved;struct spd_xiicps adapter;
 struct spd_transport transport;struct spd_reader reader;struct spd_page_transfer page_op;
 enum spd_page saved_page;enum spd_session_result result;
 uint64_t deadline,last_now;unsigned polls,phase;
 int started,stopped,capture_error,page_restored,controller_restored;
};
static void spd_session_stop(struct spd_session *s,enum spd_session_result result) {
 s->result=result;s->stopped=1;
}
static int spd_session_page(struct spd_session *s,enum spd_page_operation op,uint64_t now) {
 if(spd_page_begin(&s->page_op,s->dev,op,now,1,1)) {
  spd_session_stop(s,SPD_SESSION_OUTER_RESTORE_REQUIRED);return -1;
 }
 return 0;
}
/* Zero-initialize once; this object and all callback storage must outlive outer
 * restoration after failure. No retries or automatic session reuse. */
static int spd_session_begin(struct spd_session *s,XIicPs *dev,uint64_t now,
                             int exclusive_no_gic,int independent_identity) {
 if(!s || s->started)return -1;
 memset(s,0,sizeof(*s));s->started=1;s->saved_page=SPD_PAGE_UNKNOWN;
 if(!independent_identity || !exclusive_no_gic || now>UINT64_MAX-3000000 ||
    spd_amd_snapshot(&s->saved,dev,exclusive_no_gic)) {
  spd_session_stop(s,SPD_SESSION_NOT_ADMITTED);return -1;
 }
 s->dev=dev;s->deadline=now+3000000;s->last_now=now;
 return spd_session_page(s,SPD_QUERY_PAGE,now);
}
static void spd_session_tick(struct spd_session *s,uint64_t now) {
 if(s->stopped)return;
 if(now<s->last_now || now>=s->deadline || ++s->polls>200000) {
  spd_session_stop(s,SPD_SESSION_OUTER_RESTORE_REQUIRED);return;
 }
 s->last_now=now;
 if(s->phase==3) {
  spd_reader_tick(&s->reader,now);
  if(!s->reader.stopped)return;
  if(s->reader.result!=SPD_PASS || !s->reader.page_restored)s->capture_error=1;
  if(s->adapter.active || s->adapter.poisoned || !spd_amd_quiet(s->dev)) {
   spd_session_stop(s,SPD_SESSION_OUTER_RESTORE_REQUIRED);return;
  }
  s->phase=4;
  spd_session_page(s,s->saved_page==SPD_PAGE_ONE?SPD_SELECT_ONE:SPD_SELECT_ZERO,now);return;
 }
 spd_page_tick(&s->page_op,now);
 if(!s->page_op.stopped)return;
 if(s->page_op.failed) {spd_session_stop(s,SPD_SESSION_OUTER_RESTORE_REQUIRED);return;}
 switch(s->phase) {
 case 0:
  s->saved_page=s->page_op.page;s->phase=1;spd_session_page(s,SPD_SELECT_ZERO,now);break;
 case 1:
  s->phase=2;spd_session_page(s,SPD_QUERY_PAGE,now);break;
 case 2:
  if(s->page_op.page!=SPD_PAGE_ZERO) {
   s->capture_error=1;s->phase=4;
   spd_session_page(s,s->saved_page==SPD_PAGE_ONE?SPD_SELECT_ONE:SPD_SELECT_ZERO,now);break;
  }
  if(spd_amd_bind(&s->adapter,s->dev,1,&s->transport)) {
   spd_session_stop(s,SPD_SESSION_OUTER_RESTORE_REQUIRED);break;
  }
  s->phase=3;spd_reader_init(&s->reader,s->transport,now,1);break;
 case 4:
  s->phase=5;spd_session_page(s,SPD_QUERY_PAGE,now);break;
 case 5:
  s->page_restored=s->page_op.page==s->saved_page;
  /* A page mismatch is still reported even if the controller can be restored. */
  if(!s->adapter.dev)s->adapter.dev=s->dev;
  s->controller_restored=spd_amd_restore(&s->saved,&s->adapter,1)==0;
  if(!s->page_restored || !s->controller_restored)spd_session_stop(s,SPD_SESSION_OUTER_RESTORE_REQUIRED);
  else spd_session_stop(s,s->capture_error?SPD_SESSION_FAILED_RESTORED:SPD_SESSION_READS_RESTORED);
  break;
 default:spd_session_stop(s,SPD_SESSION_OUTER_RESTORE_REQUIRED);
 }
}
#endif
