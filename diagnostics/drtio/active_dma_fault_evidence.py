"""Strict active-fault telemetry checks, not a hardware runner; LGPL-3.0-or-later."""
import re


def validate(aux, kernel, *, expected_timestamp, edge_before, edge_after,
             read_requests, read_completions):
    """Counter arguments must come from independent leased hardware snapshots.

    Synthetic fixtures qualify this parser only, never hardware or TTL behavior.
    Restoration is an additional mandatory check owned by the parent wrapper.
    """
    def one(pattern):
        matches=list(re.finditer(pattern,aux,re.M))
        if len(matches)!=1:raise ValueError('Missing/duplicate fault evidence: '+pattern)
        return matches[0]
    arm=one(r'^AUX_DDMA LAB_ARM result=0 cycles=250000\r?$')
    active=one(r'^AUX_DDMA LAB_ACTIVE id=(\d+) accepted=(\d+) completed=(\d+) triggers=1\r?$')
    complete=one(r'^AUX_DDMA LAB_COMPLETE id=(\d+) raw=4 channel=0 timestamp=([0-9a-fA-F]{16}) accepted=(\d+) completed=(\d+) faulted=1\r?$')
    ident=active[1]
    status=one(r'^AUX_DDMA STATUS id='+ident+r' error=(\d+)\r?$')
    play=one(r'^AUX_DDMA REPLY kind=181 id='+ident+r' succeeded=(\d+)\r?$')
    if status[1]!='1' or play[1]!='1':raise ValueError('Native underflow status and accepted playback required')
    if not (arm.start()<play.start()<status.start() and arm.start()<active.start()<status.start()<complete.start()):
        raise ValueError('Fault markers do not follow arm/admission/active/status/completion')
    if (complete[1]!=ident or int(complete[2],16)!=expected_timestamp or
        int(complete[3])!=int(active[2]) or int(complete[4])!=int(active[3])+1 or
        int(active[2])!=int(active[3])+1):
        raise ValueError('Identity/timestamp or accepted/completed conservation mismatch')
    caught=re.findall(r'^NATIVE_DDMA_ACTIVE_UNDERFLOW_CAUGHT_PASS timestamp=(\d+)\r?$',kernel,re.M)
    if len(caught)!=1 or int(caught[0])!=expected_timestamp:
        raise ValueError('Missing/mismatching caught native underflow timestamp')
    if any(t in kernel for t in ('ConnectionResetError','Previous kernel did not cleanly finish')):
        raise ValueError('Kernel session did not finish cleanly')
    if any(t in aux for t in ('AUX_DDMA INTERNAL_ERROR','AUX_FW PANIC','AUX_DDMA FAIL_CLOSED')):
        raise ValueError('Unexpected firmware/internal failure')
    counters=(edge_before,edge_after,read_requests,read_completions,expected_timestamp)
    if any(type(n) is not int or n<0 for n in counters):raise ValueError('Nonnegative independent integer counters required')
    if edge_before!=edge_after or not read_requests or read_requests!=read_completions:
        raise ValueError('TTL activity or incomplete AXI drain')
    return dict(status='ACTIVE_FAULT_EVIDENCE_PASS',id=int(ident),raw_error=4,
                aux_error=1,timestamp=expected_timestamp,accepted=int(active[2]),completed=int(complete[4]),
                restoration='PARENT_MUST_VERIFY')


def validate_logged_metrics(aux,kernel,*,expected_timestamp):
    """Consume firmware reads of the independent hardware counters.

    Caller must also prove artifact/map identity, continuous clock/reset epoch,
    pad settling and final restoration. These counters are not ARTIQ software
    event counts; they are separate RTL handshake/pad counters.
    """
    def sample(label):
        matches=list(re.finditer(r'^AUX_DDMA '+label+r' ar=(\d+) rlast=(\d+) edges=(\d+)\r?$',aux,re.M))
        if len(matches)!=1:raise ValueError('Missing/duplicate independent metrics '+label)
        values=tuple(int(n) for n in matches[0].groups())
        if any(n>=2**32 for n in values):raise ValueError('Counter exceeds 32-bit CSR')
        return matches[0],values
    before,b=sample('LAB_BASELINE');after,a=sample('LAB_METRICS')
    arm=aux.find('AUX_DDMA LAB_ARM result=0')
    complete=aux.find('AUX_DDMA LAB_COMPLETE')
    status=aux.find('AUX_DDMA STATUS')
    if not before.start()<arm<status<after.start()<complete:
        raise ValueError('Independent counter snapshot order invalid')
    requests=(a[0]-b[0])&0xffffffff;completions=(a[1]-b[1])&0xffffffff
    return validate(aux,kernel,expected_timestamp=expected_timestamp,edge_before=b[2],edge_after=a[2],
                    read_requests=requests,read_completions=completions)
