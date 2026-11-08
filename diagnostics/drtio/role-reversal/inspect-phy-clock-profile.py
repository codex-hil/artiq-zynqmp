#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Pin actual generated IP clock profile, rejecting unreviewed frequency changes."""
import argparse,json,hashlib
from pathlib import Path

def inspect(path):
 raw=path.read_bytes();d=json.loads(raw)
 parameters=d['ip_inst']['parameters']['component_parameters']
 keys=('TX_LINE_RATE','RX_LINE_RATE','TX_REFCLK_FREQUENCY','RX_REFCLK_FREQUENCY',
       'TX_USER_DATA_WIDTH','RX_USER_DATA_WIDTH','FREERUN_FREQUENCY')
 values={key:float(parameters[key][0]['value']) for key in keys}
 expected=dict(TX_LINE_RATE=2.5,RX_LINE_RATE=2.5,TX_REFCLK_FREQUENCY=156.25,
               RX_REFCLK_FREQUENCY=156.25,TX_USER_DATA_WIDTH=20,RX_USER_DATA_WIDTH=20,
               FREERUN_FREQUENCY=125)
 if values!=expected:raise ValueError('Unreviewed PHY clock/profile change: '+str(values))
 return {'kind':'PINNED_IP_CLOCK_CONTRACT_NOT_MEASURED_HARDWARE',
         'xci_sha256':hashlib.sha256(raw).hexdigest(),'parameters':values,
         'periods_ns':{'management_pl_clk0':8.0,'gt_reference_ref_p':6.4,
                       'native_raw20_tx_expected':8.0,'native_raw20_rx_expected':8.0},
         'limits':['GTref156.25 differs from125MHzfreerun/DRP','Nativeperiods expected fromline2.5Gbps/raw20 not physicalmeasurement',
                   'No CDC exceptions or reset-pin false paths authorized by this contract']}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('xci',type=Path);a=p.parse_args()
 print(json.dumps(inspect(a.xci),indent=2))
