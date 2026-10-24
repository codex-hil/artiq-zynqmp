"""RF envelope measurements from existing CH3/4 scope records, no scope writes."""
import numpy as np
from scipy.signal import hilbert
from scipy.ndimage import binary_closing


def analyze(capture, reference, kind):
    result = {}
    period = 64/153600000
    for ch, data in capture['channels'].items():
        if data['clipped']:raise ValueError('Clipped RF record')
        y = np.array(data['curve']);dt = data['sample_interval_s']
        t = np.arange(len(y))*dt
        z = hilbert(y-np.mean(y))
        amplitude = 2*abs(z)/reference['channels'][ch]['fit_vpp']
        # Keep FFT edge transients away from the accepted measurements.
        valid = (t > 100e-9) & (t < t[-1]-100e-9)
        expected_period = period/2 if kind == 'phase' else period
        # Lag fit is robust to plateau ripple and arbitrary acquisition phase.
        first, last = np.flatnonzero(valid)[[0, -1]]
        lags = np.arange(int(expected_period*.9/dt), int(expected_period*1.1/dt)+1)
        errors = [np.mean((amplitude[first:last-lag]-amplitude[first+lag:last])**2) for lag in lags]
        measured = float(lags[np.argmin(errors)]*dt)
        if abs(measured/expected_period-1) > .02:raise ValueError(('Envelope repetition period', measured, expected_period))
        item = {'period_s': measured, 'expected_period_s': expected_period}
        if kind == 'levels':
            # Centers of the full/zero/half/zero plateaus relative to each peak.
            # Peaks wander on flat tops, so classify interior samples by local derivative.
            smooth = np.convolve(amplitude, np.ones(31)/31, mode='same')
            flat = abs(np.gradient(smooth, dt)) < 1e6
            values = []
            for target in (0, .5, 1):
                selected = amplitude[valid & flat & (abs(smooth-target) < .10)]
                if len(selected) < 100:raise ValueError(('Missing plateau', ch, target))
                level = float(np.median(selected));values.append(level)
                if abs(level-target) > .06:raise ValueError(('Wrong plateau', level, target))
            item['normalized_levels'] = values
        elif kind == 'phase':
            high = binary_closing(amplitude > .8, structure=np.ones(int(10e-9/dt), dtype=bool)) & valid
            edges = np.flatnonzero(np.diff(high.astype(int), prepend=0) == 1)
            ends = np.flatnonzero(np.diff(high.astype(int), append=0) == -1)
            carrier = reference['channels'][ch]['fit_hz']
            baseband = z*np.exp(-2j*np.pi*carrier*t)
            phasors = []
            for start in edges:
                end = next((v for v in ends if v > start), start)
                trim = int(15e-9/dt)
                if end-start < int(60e-9/dt):continue
                phasors.append(np.mean(baseband[start+trim:end-trim]))
            delta = np.angle(np.array(phasors[1:])*np.conj(phasors[:-1]))
            if len(delta) < 4 or np.max(abs(abs(delta)-np.pi/2)) > .20:
                raise ValueError(('Complex envelope phase', delta.tolist()))
            item['adjacent_pulse_phase_degrees'] = np.degrees(delta).tolist()
        elif kind == 'gaussian':
            # Search only phase of the known 64-clock waveform; no free width fit.
            errors = []
            for shift in np.linspace(0, period, 1025):
                index = ((t-shift)%period)/period*64
                target = np.exp(-.5*((index-32)/10)**2)
                errors.append(float(np.sqrt(np.mean((amplitude[valid]-target[valid])**2))))
            item['normalized_shape_rmse'] = min(errors)
            if min(errors) > .10:raise ValueError(('Gaussian shape', min(errors)))
        result[ch] = item
    return result
