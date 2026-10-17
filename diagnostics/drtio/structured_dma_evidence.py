"""Require a real structured master DMA exception; LGPL-3.0-or-later."""


def structured_rejection_result(host_log,master_log,recovery_log):
    if ('DMAError' not in host_log or
            'Failed to upload distributed DMA trace' not in host_log or
            'DDMA upload rejected:' not in master_log):
        raise RuntimeError('Missing structured DMAError and concrete master rejection')
    if ('ConnectionResetError' in host_log or 'session aborted:' in master_log or
            'Previous kernel did not cleanly finish' in recovery_log):
        raise RuntimeError('Upload rejection still aborted the session')
    return dict(native_ddma_structured_error='PASS',
        native_ddma_host_exception='DMAError',native_ddma_clean_exception_recovery='PASS')
