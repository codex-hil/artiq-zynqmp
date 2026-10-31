/* SPDX-License-Identifier: LGPL-3.0-or-later */
#if !defined(__MICROBLAZE__) || !defined(ARTIQ_PIT_TERMINAL_AUDIT_ONLY) || !defined(ARTIQ_PIT_MMIO_AUDIT_ONLY) || !defined(ARTIQ_PIT_IRQ_AUDIT_ONLY)
#error "Explicit MicroBlaze terminal/MMIO/IRQ audit opt-ins required; no deployment"
#endif
#include "pit_digest_compose.h"
#include "pit_irq_audit.h"
#include "pit_mmio_read.h"
#include "pit_ro_adapter.h"
#include "pit_mailbox_publish_audit.h"
extern __attribute__((noreturn)) void pit_terminal_audit(void);
static struct pit_ro_adapter digest_read_adapter;
static int digest_ordered_read(void *ctx,uint32_t address,uint32_t *out)
{
 if(ctx)return -1;
 return pit_ro_read(&digest_read_adapter,address,out);
}
/* Separate retained audit entry only. No main/request hook or RAM consumer.
 * Partial preparation failure is terminal; no retry/reset/rearm here. */
__attribute__((noinline,noreturn,used)) void pit_digest_root_audit(struct pit_digest_plan *plan)
{
 unsigned i;
 uint32_t image_nonzero=0;
 if(!plan||plan->consumed||!plan->nonce||!plan->image_digest||plan->capture_context||
    plan->receipt_context||plan->ops.msr||plan->ops.disable||plan->ops.read||
    plan->ops.write||plan->ops.barrier||plan->ops.terminal||plan->receipt_write||
    plan->receipt_barrier||plan->lifecycle_status||plan->metadata_status||plan->publication_status)
  pit_terminal_audit();
 for(i=0;i<96;i++)if(((const volatile unsigned char *)&plan->record)[i])pit_terminal_audit();
 for(i=0;i<8;i++)image_nonzero|=plan->image_digest[i];
 if(!image_nonzero||pit_ro_prepare(&digest_read_adapter,pit_mmio_read,0)||pit_mailbox_prepare_audit())
  pit_terminal_audit();
 plan->ops.msr=pit_irq_msr_audit;plan->ops.disable=pit_irq_disable_audit;
 plan->ops.read=digest_ordered_read;
 plan->ops.write=pit_mailbox_sample_write_audit;plan->ops.barrier=pit_mailbox_sample_barrier_audit;
 plan->receipt_write=pit_mailbox_terminal_write_audit;plan->receipt_barrier=pit_mailbox_terminal_barrier_audit;
 (void)pit_digest_compose(plan);
 pit_terminal_audit();
}
