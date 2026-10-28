# SPDX-License-Identifier: LGPL-3.0-or-later
"""Abstract hostile sleep/wake schedules, no transport or hardware simulation."""
import itertools,json
def model():
 traces=[]
 for middle in itertools.product((False,True),repeat=3):
  states=(True,*middle,True)
  # Sleep sampled at both endpoints; external RAM transaction spans interior.
  unsafe=not all(states[1:4])
  traces.append({'sleep_states':states,'both_polls_report_sleep':True,'continuous_sleep_during_ram':not unsafe})
 assert len(traces)==8 and sum(not t['continuous_sleep_during_ram'] for t in traces)==7
 return {'hardware_executed':False,'deployable':False,'abstract_schedules':traces,'counterexamples':7,'limits':'Combinatorial counterexample only. Assumes wake/resleep can occur; does not model actual event timing, register synchronisation or identify a real board failure. Endpoint sleep polls cannot prove an interval property without separately excluding wake.'}
if __name__=='__main__':print(json.dumps(model(),indent=2))
