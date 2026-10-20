"""Exact endpoint extraction and omission negatives; LGPL-3.0-or-later."""
import unittest
from dma_cdc_constraints import dma_crossings,dma_tcl


class ConstraintsTests(unittest.TestCase):
    def fixture(self):
        specs=[('p_dmacsr_offset1',64),('p_dmacsr_crimaster_error_w',2),
            ('p_dmacsr_crimaster_error_channel_status',24),
            ('p_dmacsr_crimaster_error_timestamp_status',64),
            ('p_dmacsr_dmarawcdc_graycounter0_q',5),
            ('p_dmacsr_dmarawcdc_graycounter1_q',5),
            ('p_tscsnapshot_graycounter0_q',3),('p_tscsnapshot_graycounter1_q',3)]
        hdl='\n'.join('reg [{}:0] {} = 0;\n{}_sink <= {};'.format(w-1,n,n,n) for n,w in specs)
        marked=[(str(w-1),n+'_sink') for n,w in specs]
        return hdl,marked

    def test_snapshot_exact_and_legacy(self):
        hdl,marked=self.fixture();g=dma_crossings(hdl,marked,snapshot=True)
        self.assertEqual((len(g),sum(x['bits'] for x in g)),(8,170))
        t=dma_tcl(g)
        self.assertIn('!= 170',t)
        for item in g:
            self.assertIn(item['first_stage'],t)
            self.assertEqual(item['max_delay_ns'],8)
        self.assertEqual(len(dma_crossings(hdl,marked)),6)

    def test_missing_or_wrong_width_rejected(self):
        hdl,marked=self.fixture()
        with self.assertRaises(ValueError):dma_crossings(hdl,marked[:-1],snapshot=True)
        marked[-1]=('3',marked[-1][1])
        with self.assertRaises(ValueError):dma_crossings(hdl,marked,snapshot=True)

    def test_lab_metrics_requires_exact_gray_crossing(self):
        hdl,marked=self.fixture()
        with self.assertRaises(ValueError):dma_crossings(hdl,marked,snapshot=True,lab_metrics=True)
        name='diagnostic_rtio_rx_gray_source'
        hdl+='\nreg [31:0] '+name+' = 0;\nmetric_sink <= '+name+';'
        marked.append(('31','metric_sink'))
        groups=dma_crossings(hdl,marked,snapshot=True,lab_metrics=True)
        self.assertEqual((len(groups),sum(g['bits'] for g in groups)),(9,202))
        self.assertEqual(groups[-1]['kind'],'gray')
        self.assertIn('metric_sink',dma_tcl(groups))
        marked[-1]=('30','metric_sink')
        with self.assertRaises(ValueError):dma_crossings(hdl,marked,snapshot=True,lab_metrics=True)
