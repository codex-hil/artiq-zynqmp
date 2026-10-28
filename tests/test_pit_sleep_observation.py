# SPDX-License-Identifier: LGPL-3.0-or-later
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/ddr'))
import pit_sleep_observation as observer
class Tests(unittest.TestCase):
    def sample(self,value=0x10000):
        return dict(version=1,nonce=7,address=observer.ADDRESS,return_code=0,value=value)
    def test_states_never_authorize_ram(self):
        for value,state in [(0,'ACTIVE_SAMPLED'),(0x10000,'SLEEP_SAMPLED'),(0xffffffff,'SLEEP_SAMPLED')]:
            result=observer.decode(self.sample(value),7)
            self.assertEqual(result['state'],state)
            for key in ['sample_authenticated','continuous_sleep_proven','pmu_ram_access_allowed','recovery_qualified','deployable','hardware_executed']:
                self.assertIs(result[key],False)
            with self.assertRaises(ValueError):observer.require_pmu_ram_access(result,interval_proven=True,recovery_qualified=True)
    def test_failed_reads_cannot_supply_plausible_value(self):
        for rc in [-1,1]:
            sample=self.sample();sample.update(return_code=rc,value=None)
            self.assertEqual(observer.decode(sample,7)['state'],'UNKNOWN')
            sample['value']=0x10000
            with self.assertRaises(ValueError):observer.decode(sample,7)
    def test_strict_input_and_no_claim_overrides(self):
        changes=[('version',True),('nonce',True),('nonce',8),('address',True),('address',0xffdc0050),('address',0xffd40044),('return_code',False),('value',True),('value',-1),('value',1<<32),('deployable',True),('continuous_sleep_proven',True),('hardware_executed',True)]
        for key,value in changes:
            bad=self.sample();bad[key]=value
            with self.assertRaises(ValueError,msg=key):observer.decode(bad,7)
        for key in self.sample():
            bad=self.sample();del bad[key]
            with self.assertRaises(ValueError):observer.decode(bad,7)
    def test_nonce_and_input_ownership(self):
        sample=self.sample();original=copy.deepcopy(sample)
        observer.decode(sample,7);self.assertEqual(sample,original)
        for nonce in [True,0,-1,1<<64]:
            with self.assertRaises(ValueError):observer.decode(sample,nonce)
if __name__=='__main__':unittest.main()
