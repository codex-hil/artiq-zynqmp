"""Bounded envelope qualification; restores shared golden image under same lease."""
import argparse
import fcntl
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from hardware_session import HardwareSession, GOLDEN, GOLDEN_SHA, HERE
from envelope_client import EnvelopePhaser
from client import Phaser
from envelope_fit import analyze
from verify_envelope_build import verify
sys.path.insert(0, str(HERE.parent/'jesd-probe'))
from rf_scope import Scope, Transport


def save(path, obj):path.write_text(json.dumps(obj, indent=2)+'\n')



class CheckedScope(Scope):
    def __init__(self, output):self.output = output

    def __exit__(self, *args):
        super().__exit__(*args)
        if not self.saved:return
        with Transport(dict(kind='tcp', host='192.168.2.15', port=4000, timeout=4)) as io:
            restored = {k:io.query(k+'?') for k in self.saved}
            untouched = {k:io.query(k+'?') for k in getattr(self, 'untouched', {})}
        save(self.output/'scope-settings-restored.json', restored)
        save(self.output/'scope-unchanged.json', untouched)
        assert restored == self.saved, 'Scope settings restoration mismatch'
        assert untouched == getattr(self, 'untouched', {}), 'Shared scope settings changed'


def validate_cw(capture):
    for ch, value in capture['channels'].items():
        expected = {'3':149e6, '4':151e6}[ch]
        assert not value['clipped'] and abs(value['fit_hz']-expected) < 50000
        assert .35 < value['fit_vpp'] < .6 and value['residual_rms'] < .03


def qualify_arm(c, scope, output):
    """ABI2 IPbus-only checks; no RTIO START or DRTIO claim."""
    tokens = []
    blocked = []
    for iteration in range(3):
        c.load([(153600000, 1, .5)])
        token = c.arm(5)
        tokens.append(token)
        if iteration:
            assert token == (tokens[-2]+1)&0x3fffffff, 'ARM token did not advance'
        status = c.playback_status()
        assert status['busy'] and status['mode'] and not status['playing']
        for address, value in ((0x400, 123), (0x23, 2), (0x24, 2),
                               (0x25, 1), (0x14, 1)):
            response = c.transact(1, address, [value], allow_error=True)
            assert response[1]&15, 'Write accepted during ARM: '+hex(address)
            blocked.append(address)
        assert c.read(0x400)[0] == 153600000
        assert c.read(0x23, 2) == [1, 5]
        capture = scope.capture('armed-zero-'+str(iteration))
        save(output/('scope-armed-zero-'+str(iteration)+'.json'), capture)
        assert all(v['fit_vpp'] < .005 for v in capture['channels'].values())
        assert c.read(0x27, 2) == [1, token], 'ARM changed without trigger'
        assert not c.playback_status()['playing']
        assert c.abort()['result'] == 1
        assert c.read(0x27)[0] == 0
        capture = scope.capture('arm-aborted-zero-'+str(iteration))
        save(output/('scope-arm-aborted-zero-'+str(iteration)+'.json'), capture)
        assert all(v['fit_vpp'] < .005 for v in capture['channels'].values())
        c.bypass()
        capture = scope.capture('arm-recovered-cw-'+str(iteration))
        save(output/('scope-arm-recovered-cw-'+str(iteration)+'.json'), capture)
        validate_cw(capture)
    c.load([(1, 1, 1)])
    c.write(0x400, [0])  # Invalid hardware entry, bypassing host validation.
    try:
        c.arm()
    except RuntimeError:
        status = c.playback_status()
        assert not status['busy'] and status['result'] == 2
        assert c.read(0x27)[0] == 0
    else:
        raise AssertionError('ARM accepted a zero-duration program')
    invalid_token = c.read(0x28)[0]
    assert invalid_token == (tokens[-1]+1)&0x3fffffff
    c.bypass()
    return {'tokens':tokens, 'blocked_addresses':blocked, 'cycles':3,
            'invalid_program_rejected':True, 'invalid_attempt_token':invalid_token,
            'rtio_start':'NOT_RUN', 'drtio':'NOT_RUN'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('bit', type=Path);p.add_argument('--sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--profile', choices=['envelope','armed'], default='envelope');a = p.parse_args()
    implementation = verify(a.bit.parent, a.profile)
    assert implementation['bit_sha256'] == a.sha256
    assert a.output.is_absolute()
    assert hashlib.sha256(a.bit.read_bytes()).hexdigest() == a.sha256
    assert hashlib.sha256(GOLDEN.read_bytes()).hexdigest() == GOLDEN_SHA
    a.output.mkdir(parents=True, exist_ok=False)
    save(a.output/'implementation.json', implementation)
    state = Path('/home/codex-hil/.cache/alinx-210512180081.state.json')
    result = {'candidate_sha256':a.sha256, 'restored_sha256':GOLDEN_SHA, 'tests':{}, 'status':'RUNNING'}
    with open('/home/codex-hil/.cache/mso4104-C020817.lock', 'a+') as sl:
        fcntl.flock(sl, fcntl.LOCK_EX|fcntl.LOCK_NB)
        with open('/home/codex-hil/.cache/alinx-210512180081.lock', 'a+') as bl:
            fcntl.flock(bl, fcntl.LOCK_EX|fcntl.LOCK_NB)
            previous = json.loads(state.read_text());save(a.output/'shared-state-before.json', previous)
            c = Phaser()
            try:
                identity = c.identify()
                if identity['abi'] != 0x10000:raise RuntimeError('Shared image changed; reassess restoration before borrowing')
                save(a.output/'before.json', {'identity':identity, 'status':c.read(0x10, 4), 'held':c.read(0x200, 21)})
            finally:c.close()
            with CheckedScope(a.output) as scope, HardwareSession(a.output) as hw:
                save(a.output/'scope-before.json', {'saved':scope.saved, 'untouched':scope.untouched})
                try:
                    hw.program(a.bit, a.sha256, 'candidate-program')
                    hw.warm_start('candidate')
                    c = EnvelopePhaser()
                    try:
                        c.require_envelope()
                        assert c.identify()["abi"] == (0x10002 if a.profile == "armed" else 0x10001)
                        ref = scope.capture('cw');validate_cw(ref);save(a.output/'scope-cw.json', ref)
                        if a.profile == 'armed':
                            result['tests']['arm_abort_rearm'] = qualify_arm(c, scope, a.output)
                            save(a.output/'arm-results.json', result['tests']['arm_abort_rearm'])
                        programs = {
                            'levels':[(16, 0, 0), (16, .5, .5), (16, 0, 0), (16, 1, 1)],
                            'phase':[(16, 0, 0), (16, 1, 1), (16, 0, 0), (16, 1j, 1j)],
                            'gaussian':[(1, math.exp(-.5*((k-31.5)/10)**2), math.exp(-.5*((k-31.5)/10)**2)) for k in range(64)]}
                        for kind, program in programs.items():
                            c.load(program);c.start(24000000)  # 10 seconds, always finite.
                            assert c.playback_status()['busy']
                            error = c.transact(1, 0x400, [123], allow_error=True)
                            assert error[1]&15, 'RAM write must fail during playback'
                            capture = scope.capture(kind);save(a.output/('scope-'+kind+'.json'), capture)
                            assert c.playback_status()['busy'], 'Playback finished before measurement'
                            result['tests'][kind] = analyze(capture, ref, kind)
                            status = c.abort();assert status['result'] == 1
                            zero = scope.capture(kind+'-zero');save(a.output/('scope-'+kind+'-zero.json'), zero)
                            assert all(v['fit_vpp'] < .005 for v in zero['channels'].values())
                            print('ENVELOPE_PASS', kind, result['tests'][kind], flush=True)
                        c.load([(153600000, 1, .5)]);c.start(5)
                        independent = scope.capture('independent')
                        save(a.output/'scope-independent.json', independent)
                        result['tests']['independent'] = {}
                        for ch, target in [('3', 1), ('4', .5)]:
                            ratio = independent['channels'][ch]['fit_vpp']/ref['channels'][ch]['fit_vpp']
                            assert abs(ratio-target) < .06
                            result['tests']['independent'][ch] = ratio
                        c.abort()
                        c.load([(1, 0, 0)]*256);c.start(0xffffffff)
                        assert c.playback_status()['busy']
                        assert c.read(0x24)[0] == 0xffffffff
                        c.abort()
                        result['tests']['full_ram_and_32bit_repeat_abort'] = True
                        # Natural finite completion, held zero, then explicit CW bypass.
                        c.load([(1, 1, 0), (1, 0, 1)]);c.start(5)
                        assert c.wait()['result'] == 0
                        completed = scope.capture('completed-zero')
                        save(a.output/'scope-completed-zero.json', completed)
                        assert all(v['fit_vpp'] < .005 for v in completed['channels'].values())
                        c.load([(1, 1, 1), (1, 1, 1)])
                        c.write(0x404, [0])  # Deliberately invalid raw hardware program.
                        c.start()
                        try:c.wait()
                        except RuntimeError:
                            assert c.playback_status()['result'] == 2
                        else:raise AssertionError('Zero-duration program accepted')
                        result['tests']['invalid_duration_rejected'] = True
                        c.bypass()
                        recovered = scope.capture('bypass');validate_cw(recovered)
                        save(a.output/'scope-bypass.json', recovered)
                        assert c.read(0x10)[0]&511 == 511
                        result['status'] = 'PHYSICAL_ENVELOPE_PASS'
                    finally:c.close()
                except BaseException as error:
                    result['status'] = 'FAIL';result['error'] = repr(error)
                    raise
                finally:
                    try:
                        hw.program(GOLDEN, GOLDEN_SHA, 'restore-program')
                        hw.warm_start('restore')
                        restored = scope.capture('restored');validate_cw(restored)
                        save(a.output/'scope-restored-rf.json', restored)
                        c = Phaser()
                        try:
                            result['restoration'] = {'identity':c.identify(), 'status':c.read(0x10, 4)}
                            assert result['restoration']['status'][0]&511 == 511
                        finally:c.close()
                        shared = {'updated_utc':datetime.now(timezone.utc).isoformat(),
                                  'owner':'alinx-phaser-envelope', 'thread':'alinx-phaser-envelope',
                                  'station':'greg-OptiPlex-3070', 'cable':'210512180081',
                                  'status':'PHASER_JESD_IPBUS_RF_RESTORED', 'bitstream':str(GOLDEN),
                                  'sha256':GOLDEN_SHA, 'configuration':'CW149/151MHz, ASF32767, main NCO150MHz',
                                  'outcome':result['status'], 'restoration':result['restoration'],
                                  'evidence':str(a.output), 'lease_released_after_completion':True}
                        temp = state.with_suffix('.tmp');save(temp, shared);temp.replace(state)
                    except BaseException as error:
                        result['restoration_error'] = repr(error)
                        temp = state.with_suffix('.tmp');save(temp, {'updated_utc':datetime.now(timezone.utc).isoformat(), 'owner':'alinx-phaser-envelope', 'status':'RESTORATION_FAILED_INSPECT_EVIDENCE', 'evidence':str(a.output)});temp.replace(state)
                        raise
                    finally:save(a.output/'status.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':main()
