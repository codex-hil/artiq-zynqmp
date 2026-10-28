# SPDX-License-Identifier: LGPL-3.0-or-later
import itertools,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'diagnostics/ddr'))
from pit_sleep_lifetime import Lifetime, INVALIDATING_EVENTS
from pit_sleep_observation import ADDRESS

def sample(nonce=7,value=0x10000):return dict(version=1,nonce=nonce,address=ADDRESS,return_code=0,value=value)
class Tests(unittest.TestCase):
    def test_all_short_event_sequences_stay_invalid_and_never_admit(self):
        alphabet=sorted(INVALIDATING_EVENTS)+['sample']
        for length in range(5):
            for seq in itertools.product(alphabet,repeat=length):
                life=Lifetime(7);seen=False
                for event in seq:
                    if event=='sample':r=life.observe(sample())
                    else:r=life.event(event);seen=True
                    self.assertEqual(r['invalidated'],seen)
                    for key in ['continuous_sleep_proven','pmu_ram_access_allowed','sample_authenticated','recovery_qualified','deployable','hardware_executed']:self.assertIs(r[key],False)
    def test_late_sleep_and_mutated_report_cannot_resurrect(self):
        life=Lifetime(7);life.observe(sample());r=life.event('wake');r['invalidated']=False;r['pmu_ram_access_allowed']=True
        r=life.observe(sample());self.assertTrue(r['invalidated']);self.assertEqual(r['first_invalidation'],'wake');self.assertFalse(r['pmu_ram_access_allowed'])
    def test_bad_samples_events_and_failed_transport_poison_session(self):
        for bad in [sample(nonce=8),dict(sample(),value=True),dict(sample(),return_code=-1,value=None),sample(value=0)]:
            life=Lifetime(7)
            try:life.observe(bad)
            except ValueError:pass
            self.assertTrue(life.observe(sample())['invalidated'])
        for event in [None,True,'grant','sleep','']:
            life=Lifetime(7)
            with self.assertRaises(ValueError):life.event(event)
            self.assertTrue(life.observe(sample())['invalidated'])
    def test_closed_session_cannot_restart(self):
        life=Lifetime(7);life.close()
        for fn in [lambda:life.observe(sample()),lambda:life.event('reset'),life.close]:
            with self.assertRaises(ValueError):fn()
        self.assertTrue(life.report()['invalidated'])
if __name__=='__main__':unittest.main()
