# SPDX-License-Identifier: LGPL-3.0-or-later
"""Offline sticky invalidation model. No physical lifetime or access authority."""
from pit_sleep_observation import decode, _uint
INVALIDATING_EVENTS=frozenset(('wake','reset','debug','exception','transport_unknown','ownership_lost'))

class Lifetime:
    def __init__(self,nonce):
        self._nonce=_uint(nonce,64,True)
        self._invalidated=False
        self._closed=False
        self._reason=None
        self._last='NO_SAMPLE'
    def _invalidate(self,reason):
        self._invalidated=True
        if self._reason is None:self._reason=reason
    def _open(self):
        if self._closed:raise ValueError('observation session closed')
    def observe(self,record):
        self._open()
        try:result=decode(record,self._nonce)
        except ValueError:
            self._invalidate('malformed_or_wrong_session')
            raise
        self._last=result['state']
        if self._last!='SLEEP_SAMPLED':self._invalidate(self._last)
        return self.report()
    def event(self,name):
        self._open()
        if type(name) is not str or name not in INVALIDATING_EVENTS:
            self._invalidate('unknown_event')
            raise ValueError('unknown lifetime event')
        self._invalidate(name)
        return self.report()
    def close(self):
        self._open()
        self._closed=True
        self._invalidate('closed')
        return self.report()
    def report(self):
        return {'nonce':self._nonce,'last_sample':self._last,'invalidated':self._invalidated,
                'first_invalidation':self._reason,'closed':self._closed,
                'continuous_sleep_proven':False,'pmu_ram_access_allowed':False,
                'sample_authenticated':False,'recovery_qualified':False,
                'deployable':False,'hardware_executed':False,
                'limits':'Caller-fed event model only; unobserved events remain possible. No hardware lifetime, capture, RAM admission or recovery proof'}
