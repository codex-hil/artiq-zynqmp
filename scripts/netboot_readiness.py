"""Bounded connect-only readiness; caller holds board lease. LGPL-3.0-or-later."""
import time


def wait(connect, seconds, clock=time.monotonic, sleep=time.sleep):
    if not 0 < seconds <= 45:
        raise ValueError('Readiness deadline must be within45seconds')
    start = clock()
    attempts = []
    while True:
        left = seconds - (clock() - start)
        if left <= 0 or len(attempts) >= 15:
            return dict(status='FAIL', elapsed_seconds=clock()-start, attempts=attempts), None
        try:
            connection = connect(min(3, left))
            attempts.append(dict(elapsed_seconds=clock()-start, status='CONNECTED'))
            return dict(status='PASS', elapsed_seconds=clock()-start, attempts=attempts), connection
        except OSError as error:
            attempts.append(dict(elapsed_seconds=clock()-start, error=str(error)))
        left = seconds - (clock() - start)
        if left > 0:
            sleep(min(1, left))
