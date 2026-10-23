"""Offline protocol reference only, no MMIO/firmware admission. LGPL-3.0-or-later."""
from dataclasses import dataclass
REQUIRED=frozenset({'boot_handoff_complete','no_handler_active','scheduler_stopped',
                    'interrupt_delivery_excluded','other_core_release_excluded',
                    'pmu_memory_access_excluded','history_drained'})
@dataclass
class Model:
    boot: int
    state: str='RUNNING'
    sequence: int=0
    request_time: int=0
    def request(self,boot,sequence,now):
        if self.state!='RUNNING' or type(boot) is not int or boot!=self.boot or type(sequence) is not int or not 0<sequence<2**64 or type(now) is not int or not 0<=now<2**64:
            raise ValueError('Wrong epoch/request/state')
        self.sequence=sequence;self.request_time=now;self.state='REQUESTED'
    def observe(self,claims,now,deadline):
        if self.state!='REQUESTED':raise ValueError('No pending request')
        if type(now) is not int or now<self.request_time or type(deadline) is not int or not 0<deadline<2**63:
            self.state='REJECTED';return self.receipt()
        if now-self.request_time>=deadline:
            self.state='REJECTED';return self.receipt()
        if type(claims) is not dict or set(claims)!=REQUIRED or any(type(v) is not bool for v in claims.values()):
            self.state='REJECTED';return self.receipt()
        if all(claims.values()):self.state='PARKED_MODEL'
        return self.receipt()
    def receipt(self):
        return dict(kind='OFFLINE_PROTOCOL_MODEL_NOT_HARDWARE_ACK',boot=self.boot,
                    sequence=self.sequence,state=self.state,destructive_test_allowed=False)
    def timeout_after_ack(self):
        if self.state!='PARKED_MODEL':raise ValueError('No model ACK')
        # No transition back to running, even if host disconnects or times out.
        return self.receipt()
    def resume(self):
        raise ValueError('Resume forbidden; restore through full platform reset')

def match_receipt(receipt,boot,sequence):
    """Match modeled session only; never a live hardware write permit."""
    return (receipt.get('kind')=='OFFLINE_PROTOCOL_MODEL_NOT_HARDWARE_ACK' and
            receipt.get('boot')==boot and receipt.get('sequence')==sequence and
            receipt.get('state')=='PARKED_MODEL' and receipt.get('destructive_test_allowed') is False)
