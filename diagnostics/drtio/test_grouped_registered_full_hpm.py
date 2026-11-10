# SPDX-License-Identifier: LGPL-3.0-or-later
"""Combined candidate substitutions restricted to known common-TX test fixtures."""
import unittest
from unittest.mock import patch
from migen import Module
import test_master_integration as integration
import test_master_full_shape_fault as shape
from aux_reset_control import AuxResetControl as OriginalControl
from aux_reset_registered import AuxResetRegistered
from aux_reset_domains_grouped import AuxResetDomainsGrouped

class RegisteredCoordinatorFixture(Module):
    def __init__(self,domains):
        if domains!=5:raise ValueError('Exact five-domain fixture required')
        self.submodules.raw=raw=OriginalControl(domains)
        # Parent renames this whole sys-domain module to the live control domain.
        self.submodules.outputs=out=AuxResetRegistered(raw,control='sys')
        self.request=raw.request;self.requester_abandoned=raw.requester_abandoned
        self.domain_ready=raw.domain_ready
        self.reset=out.reset;self.admit=out.admit;self.abandonment_ready=out.abandonment_ready

def grouped_fixture(domains,*,control):
    if tuple(domains)!=('ps','sys','rtio_rx','rio','rio_phy'):
        raise ValueError('Exact fixture clock/reset policy required')
    # Actual adapter fixture uses the same tx_source; behavioral fault fixture
    # schedules SYS/rio/rio_phy at identical period+phase. Not production proof.
    return AuxResetDomainsGrouped(control=control,shared_tx_clock_confirmed=True,
                                  shared_reset_policy_confirmed=True)

class GroupedRegisteredFullHPMTests(unittest.TestCase):
    def run_candidate(self,callback):
        with patch('master_dual_ingress.AuxResetControl',RegisteredCoordinatorFixture), \
             patch('master_dual_ingress.AuxResetDomains',side_effect=grouped_fixture) as factory:
            callback()
            self.assertEqual(factory.call_count,1)
    def test_guarded_actual_adapters_two_reset_episodes_exact_multireg(self):
        self.run_candidate(lambda:integration.IntegrationTests.exercise_two_hpm_roundtrip(self,True,True))
    def test_partial_aw_bad_wlast_independent_management_recovery(self):
        self.run_candidate(lambda:shape.FullShapeFaultTests.exercise(self,'w'))
if __name__=='__main__':unittest.main()
