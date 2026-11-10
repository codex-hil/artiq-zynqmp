# SPDX-License-Identifier: LGPL-3.0-or-later
"""Test-only class substitution; original assembly defaults and manifest untouched."""
import unittest
from unittest.mock import patch
import test_master_integration as integration
import test_master_full_shape_fault as shape
from aux_reset_domains_masked import AuxResetDomainsMasked

class MaskedReadyFullHPMTests(unittest.TestCase):
    def test_actual_guarded_ps_adapters_exact_xilinx_multireg(self):
        with patch('master_dual_ingress.AuxResetDomains',AuxResetDomainsMasked):
            integration.IntegrationTests.exercise_two_hpm_roundtrip(self,True,True)

    def test_accepted_aw_bad_wlast_management_reset_fresh_write(self):
        with patch('master_dual_ingress.AuxResetDomains',AuxResetDomainsMasked):
            shape.FullShapeFaultTests.exercise(self,'w')

if __name__=='__main__':unittest.main()
