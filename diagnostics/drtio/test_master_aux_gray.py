# SPDX-License-Identifier: LGPL-3.0-or-later
"""Same native encoded link with isolated Gray AUX controllers at both ends."""
from test_master_aux import MasterAuxTests
from aux_controller_gray import GrayAuxController

class GrayMasterAuxTests(MasterAuxTests):
    controller_type=GrayAuxController

# Do not rediscover the imported baseline suite in this module.
del MasterAuxTests
