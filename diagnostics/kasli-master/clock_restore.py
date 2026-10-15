"""Bounded volatile Si5324 baseline restore lab test. LGPL-3.0-or-later.

Caller owns board locks, verified DNA/diagnostic, and mux route. No flash/OTP.
"""
import time


def exercise(comm, bus, baseline, plan, report):
    for name, expected in (('eem_enable', 0), ('gtp_control', 0), ('diag_sfp_outputs', 7)):
        if getattr(comm.regs, name).read() != expected:
            raise RuntimeError('Diagnostic outputs not disabled: ' + name)
    target = {item['register']: item['value'] for item in plan['configuration_to_compare_then_restore']}
    if set(target) & {129, 130, 134, 135, 136}:
        raise RuntimeError('Plan includes status/ID/command replay')
    if any(baseline[str(reg)] != [value, value] for reg, value in target.items()):
        raise RuntimeError('Fresh profile differs from restoration baseline')
    if baseline['136'] != [0, 0]:
        raise RuntimeError('Baseline command register not idle')
    started = time.monotonic()
    report.update(writes=[], restore_retries=[], profile_restoration='NOT_RUN')

    def retry(action, label):
        for attempt in range(3):
            if time.monotonic() - started > 120:
                raise TimeoutError('Profile restore deadline')
            try:
                return action()
            except Exception as error:
                report['restore_retries'].append({'operation': label, 'attempt': attempt, 'error': str(error)})
                if attempt == 2:
                    raise

    def write_once(reg, value, reset=False):
        try:
            bus.start()
            if not bus.put(0xd0): raise RuntimeError('address NACK')
            if not bus.put(reg): raise RuntimeError('offset NACK')
            ack = bus.put(value)
            if not ack and not reset: raise RuntimeError('value NACK')
            report['writes'].append({'register': reg, 'value': value, 'value_ack': ack})
        finally:
            bus.stop()

    def read(reg):
        return retry(lambda: bus.read(0x68, reg, 1)[0], 'read' + str(reg))

    def restore():
        for reg, value in target.items():
            retry(lambda reg=reg, value=value: write_once(reg, value), 'write' + str(reg))
        retry(lambda: write_once(136, 0x40), 'fresh ICAL')
        deadline = time.monotonic() + 20
        while True:
            status, command = read(130), read(136)
            if not status & 1 and not command & 0xc0:
                break
            if time.monotonic() > deadline:
                raise TimeoutError('PLL/calibration timeout')
            time.sleep(0.1)
        observed = {str(reg): read(reg) for reg in target}
        report['post_configuration'] = observed
        if any(observed[str(reg)] != value for reg, value in target.items()):
            raise RuntimeError('Profile readback mismatch')
        if (read(134) << 8 | read(135)) != 0x182:
            raise RuntimeError('Product ID mismatch after restore')
        report['profile_restoration'] = 'PASS'

    report['clock_configuration_written'] = True
    try:
        retry(lambda: write_once(136, 0x80, reset=True), 'soft reset')
        time.sleep(0.02)
        if (read(134) << 8 | read(135)) != 0x182:
            raise RuntimeError('Post-reset product ID mismatch')
        restore()
    except Exception:
        # One bounded recovery attempt, never reset again after partial failure.
        report['recovery_attempted'] = True
        restore()
        raise

    def gray(value):
        decoded = value
        while value:
            value >>= 1
            decoded ^= value
        return decoded

    def sample():
        before = time.monotonic()
        value = gray(comm.regs.diag_si_gray.read())
        after = time.monotonic()
        return value, (before + after) / 2

    samples = []
    for _ in range(3):
        a, ta = sample()
        time.sleep(1)
        b, tb = sample()
        samples.append(((b - a) & 0xffffffff) / (tb - ta))
    report['output_hz_against_host'] = samples
    if any(abs(hz / 125e6 - 1) > 0.01 for hz in samples):
        raise RuntimeError('Restored clock frequency outside diagnostic tolerance')
    report['restoration_profile_validated'] = True
    report['restore_test_seconds'] = round(time.monotonic() - started, 3)
