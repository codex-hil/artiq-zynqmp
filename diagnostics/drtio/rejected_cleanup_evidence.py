"""Exact rejected-cleanup/recovery evidence; LGPL-3.0-or-later."""
import re


def cleanup_recovery_result(aux,master,rejected_id):
    events=[]
    for line in aux.splitlines():
        m=re.fullmatch(r'AUX_DDMA REPLY kind=(\d+) id=(\d+) succeeded=(\d+)',line)
        if m:events.append((int(m[1]),int(m[2]),int(m[3])))
        m=re.fullmatch(r'AUX_DDMA STATUS id=(\d+) error=(\d+)',line)
        if m:events.append((182,int(m[1]),0 if int(m[2]) else 1))
    if ([e[0] for e in events]!=[179,177,181,182,179] or
            any(e[2]!=1 for e in events) or events[0][1]!=rejected_id or
            len({e[1] for e in events[1:]})!=1):
        raise RuntimeError('Expected exact rejected cleanup ACK, upload, playback/status, erase')
    if 'Error erasing trace on DMA' in master or 'error erasing DMA trace' in master:
        raise RuntimeError('Rejected cleanup still caused master erase error')
    return dict(native_ddma_rejected_cleanup='PASS',
        native_ddma_cleanup_id=rejected_id,native_ddma_recovery_id=events[1][1],
        native_ddma_cleanup_scope='identity-matched rejected erase ACK followed by normal upload/playback/status/erase; no master cleanup error')
