# SPDX-License-Identifier: LGPL-3.0-or-later
"""Offline nonce/image/terminal correlation, never a hardware admission gate."""
import re
from pit_sleep_lifetime import Lifetime
from pit_terminal_receipt import accept

class Session:
    def __init__(self,nonce,image_sha256):
        self._life=Lifetime(nonce)
        if type(image_sha256) is not str or not re.fullmatch('[0-9a-f]{64}',image_sha256) or image_sha256=='0'*64:
            raise ValueError('nonzero lowercase image SHA256 required')
        self._nonce=nonce
        self._image=image_sha256
        self._attempted=False
        self._status=None
    def observe(self,record):
        self._life.observe(record)
        return self.report()
    def event(self,name):
        self._life.event(name)
        return self.report()
    def terminal(self,first,second,samples=None):
        if self._life.report()['closed']:raise ValueError('session closed')
        if self._attempted:
            self._life.event('transport_unknown')
            raise ValueError('terminal correlation is one shot')
        self._attempted=True
        try:result=accept(first,second,self._nonce,self._image,samples)
        except ValueError:
            self._life.event('transport_unknown')
            raise
        self._status=result['status']
        return self.report()
    def close(self):
        self._life.close()
        return self.report()
    def report(self):
        return {'nonce':self._nonce,'image_sha256':self._image,
                'terminal_attempted':self._attempted,'terminal_content_bound':self._status is not None,
                'terminal_status':self._status,'lifetime':self._life.report(),
                'origin_authenticated':False,'sleep_proven':False,'pmu_ram_access_allowed':False,
                'deployable':False,'hardware_executed':False,'destructive_test_allowed':False,
                'limits':'Supplied content/session correlation only. No chronological, physical origin, continuous sleep or recovery proof'}
