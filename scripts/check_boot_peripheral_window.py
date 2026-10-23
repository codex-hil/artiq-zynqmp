"""Necessary peripheral fields only, never DDR admission; LGPL-3.0-or-later."""
def check(decoded):
    rows=decoded.get('samples', [])
    required={'gem_rx_enabled','gem_tx_enabled','sd_command_inhibit','sd_data_inhibit',
              'sd_data_active','sd_write_active','sd_read_active','qspi_dma_busy',
              'qspi_dma_outstanding','qspi_dma_fifo_level','qspi_dma_unknown_bits'}
    valid=len(rows)==2 and decoded.get('stable') is True
    for row in rows:
        valid=valid and required <= set(row) and all(
            type(row.get(k)) in (bool,int) and row[k]==0 for k in required)
    return dict(necessary_fields_pass=bool(valid),destructive_test_allowed=False,
                ownership='NOT_PROVEN',observations=decoded,
                limits='Necessary fields only; no core/PMU/PL/PCAP ownership or transaction-drain proof.')
