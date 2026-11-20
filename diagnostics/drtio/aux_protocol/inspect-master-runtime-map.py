#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Read-only source mapping, no MMIO, firmware patch or hardware admission."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--generated-main',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[3]
bindings=[]
def bind(path,anchor,meaning):
 path=Path(path);path=path if path.is_absolute() else repo/path
 text=path.read_text();assert text.count(anchor)==1,('ambiguous or missing source anchor',str(path),anchor)
 bindings.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'anchor':anchor,'line':text[:text.index(anchor)].count('\n')+1,'meaning':meaning})
bind(a.generated_main,'\t\txemacif_input(echo_netif);\n\t\ttransfer_data();\n        genesys_kernel_poll();','Candidate step belongs after existing foreground network and worker service; next iteration must return to timers. No insertion made.')
bind(a.generated_main,'\t\t\ttcp_fasttmr();','Existing foreground TCP timer service must remain reachable.')
bind('scripts/attach_a53_services.py',"if text.count('\\t\\ttransfer_data();') != 1:",'Generated-app attachment uses a unique loop anchor; do not patch maintained AMD source.')
bind('boards/genesys_zu-5ev/2_firmware_a53/c/kernel_lwip.c','int genesys_kernel_state(void) {','CPU0 software view only; no CRI ownership grant, worker quiescence handshake or lifetime reservation.')
bind('boards/genesys_zu-5ev/2_firmware_a53/c/kernel_lwip.c','int genesys_kernel_running(void) {','Conservative busy/dead/recovering flag protects existing shared latch; zero is not a DRTIO reservation.')
bind('boards/genesys_zu-5ev/2_firmware_a53/c/kernel_lwip.c','static void command(uint32_t op,uint32_t n) {','Network callbacks can dispatch worker commands before candidate turn; integration must arbitrate entire setup lifetime.')
bind('boards/genesys_zu-5ev/2_firmware_a53/c/kernel_lwip.c','void genesys_kernel_poll(void) {','Preserve mailbox/cache protocol and worker progress, never reuse mailbox for master panic publication.')
bind('boards/genesys_zu-5ev/2_firmware_a53/c/management_lwip.c','uint64_t genesys_rtio_counter(void) {','Existing diagnostic writes shared counter latch; distinct ownership/access review required.')
bind('diagnostics/drtio/aux_protocol/master_setup_cooperative.h','static inline int msc_step(','Portable candidate, at most one action or route step; no concrete foreground registration.')
bind('diagnostics/drtio/aux_protocol/test_master_setup_cooperative.c','static int action_step(','Current concrete action mapping is test-only; cannot silently use fakebus action context in runtime.')
bind('diagnostics/drtio/aux_protocol/master_rt_setup.h','static inline int mrt_set_time_once(','Set-time polls inside callback; return only means local TX completion, remote TSC still separate.')
bind('diagnostics/drtio/aux_protocol/master_rt_setup.h','static inline int mrt_buffer_once(','Force/request/unforce span callback, unknown outcomes require independent reconciliation; cannot yield by replay.')
bind('diagnostics/drtio/aux_protocol/master_aux_mmio.h','static inline int mm_read(','Callback return required; finite loop count cannot contain single hung AXI transaction.')
bind('diagnostics/drtio/aux_protocol/master_leaf_target.rs','extern "C" {fn aux_master_panic()->!;}','Production nonreturning panic hook unresolved; Linux-user test hook is not integration.')
bind('boards/genesys_zu-5ev/3_kernel/src/lib.rs','fn fail(message: &[u8]) -> ! {','Existing CPU1 failure publishes worker status then parks; not a CPU0 management-preserving panic handler.')
bind('diagnostics/drtio/role-reversal/a53/shape_recovery.h','static inline struct gsr_result gsr_recover(','Requires independent requester withdrawal and abandonment before recovery; cannot rescue caller blocked in AXI.')
actions=[('LINK','mrt_live','live read is target access, not independent watchdog'),('ECHO','aux_master_control_encode + mm_send / ma_receive_fixed','start once, then receive; sole AUX slot owner'),('SET_TIME','mrt_set_time_once','split callback polling before any latency claim'),('TSC_ACK','ma_receive_fixed + aux_master_control_decode','spontaneous remote ack; no time-set request encoding'),('ROUTING','msi_step + mq_send_checked/mq_recv_slot','256 canonical paths then rank; all ACKs do not prove peer table apply'),('STATUS','aux_master_control_encode + mm_send / ma_receive_fixed','DestinationOK is candidate observation, not admission'),('BUFFER','mrt_buffer_once','exclusive CRI over force/request/unforce, nonzero credits and exact counter delta')]
report={'status':'OFFLINE_CPU0_FOREGROUND_SOURCE_MAP_COMPLETE_RUNTIME_NOT_ADMITTED','runtime_admitted':False,'hardware_admitted':False,'bindings':bindings,'actions':[dict(action=x,backend=y,remaining=z) for x,y,z in actions],'required_before_adapter':['Explicit whole-session CRI/AUX ownership grant and release with worker dispatch interlock; idle snapshot insufficient','Concrete bounded resumable nonrouting backend callbacks; callback-count bound alone insufficient','Independent target-bus fault containment and requester withdrawal path; no synchronous target MMIO from panic','Production panic/exception policy preserving CPU0 management and CPU1 kernel roles','Fresh image/map/epoch/clock/physical link and restoration receipts; no automatic reset/reinit/drain','Ongoing health monitoring/admission revocation after setup completion, not latched success forever'],'next_safe_offline':'Prototype sole-owner foreground scheduling/worker-dispatch interlock in isolated host model; keep all target MMIO and production hooks disabled'}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(bindings),'source bindings')
