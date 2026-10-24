"""Check waveform analysis against synthetic captures, separately from hardware."""
import numpy as np
from envelope_fit import analyze


def test_known_envelopes_and_phase():
    dt = .2e-9;t = np.arange(10000)*dt
    index = ((t+37e-9)*153600000).astype(int)%64
    reference = {'channels':{}}
    for kind in ['levels', 'phase', 'gaussian']:
        capture = {'channels':{}}
        for ch, frequency in [('3', 149e6), ('4', 151e6)]:
            gain = {'levels':np.array([0, .5, 0, 1])[index//16],
                    'phase':np.array([0, 1, 0, 1j])[index//16],
                    'gaussian':np.exp(-.5*((index-31.5)/10)**2)}[kind]
            y = .24*np.real(gain*np.exp(2j*np.pi*frequency*t+.34j))
            capture['channels'][ch] = dict(curve=y.tolist(), sample_interval_s=dt, clipped=False)
            reference['channels'][ch] = dict(fit_vpp=.48, fit_hz=frequency)
        analyze(capture, reference, kind)


def test_wrong_phase_is_rejected():
    dt = .2e-9;t = np.arange(10000)*dt
    on = (((t+37e-9)*153600000).astype(int)%32) >= 16
    capture = {'channels':{}};reference = {'channels':{}}
    for ch, frequency in [('3', 149e6), ('4', 151e6)]:
        y = .24*on*np.cos(2*np.pi*frequency*t)
        capture['channels'][ch] = dict(curve=y.tolist(), sample_interval_s=dt, clipped=False)
        reference['channels'][ch] = dict(fit_vpp=.48, fit_hz=frequency)
    try:analyze(capture, reference, 'phase')
    except ValueError as error:assert 'Complex envelope phase' in str(error)
    else:raise AssertionError('Unrotated pulses falsely accepted')


if __name__ == '__main__':
    test_known_envelopes_and_phase()
    test_wrong_phase_is_rejected()
    print('SYNTHETIC_ENVELOPE_ANALYSIS_2_TESTS_PASS')
