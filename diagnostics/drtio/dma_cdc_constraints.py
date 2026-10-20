"""Exact generated-HDL DMA CDC constraints; LGPL-3.0-or-later.

Held payloads are bundled data, not independently synchronized arbitrary words.
The launch/complete handshakes must retain their RTL settling intervals.
"""
import re


def dma_crossings(hdl, marked, snapshot=False,lab_metrics=False):
    first = {name: int(width)+1 if width else 1 for width,name in marked}
    specs = [('offset1',64),('crimaster_error_w',2),
             ('crimaster_error_channel_status',24),
             ('crimaster_error_timestamp_status',64),
             ('dmarawcdc_graycounter0_q',5),('dmarawcdc_graycounter1_q',5)]
    if snapshot:
        specs += [('tscsnapshot_graycounter0_q',3),('tscsnapshot_graycounter1_q',3)]
    if lab_metrics:specs += [('rtio_rx_gray_source',32)]
    groups=[]
    for suffix,width in specs:
        prefix = (r'diagnostic_' if suffix=='rtio_rx_gray_source' else
                  r'\w*' if suffix.startswith('tscsnapshot') else r'\w*dmacsr\w*_')
        sources=re.findall(r'\breg\s*(?:\[\d+:0\]\s*)?('+prefix+suffix+r')\s*=',hdl)
        if len(sources)!=1:raise ValueError('DMA CDC source: '+suffix)
        source=sources[0]
        endpoints=[name for name in first if re.search(r'\b'+re.escape(name)+r'\s*<=\s*'+re.escape(source)+r'\s*;',hdl)]
        if len(endpoints)!=1 or first[endpoints[0]]!=width:
            raise ValueError('DMA CDC first-stage width/source: '+source)
        groups.append({'source':source,'first_stage':endpoints[0],'bits':width,
                       'kind':'gray' if 'graycounter' in suffix or suffix=='rtio_rx_gray_source' else 'held-payload',
                       'max_delay_ns':8,'bus_skew_ns':8})
    return groups


def dma_tcl(groups):
    """Must run BEFORE the general first-stage false-path command."""
    total=sum(g['bits'] for g in groups)
    lines=['set dma_timed_sync {}']
    for group in groups:
        src,dst,width=group['source'],group['first_stage'],group['bits']
        lines += [
            f'set dma_sources [get_cells -hierarchical -filter {{NAME =~ {src}_reg* && REF_NAME =~ FD*}}]',
            f'set dma_endpoints [get_cells -hierarchical -filter {{NAME =~ {dst}_reg* && REF_NAME =~ FD*}}]',
            f'if {{[llength $dma_sources] != {width} || [llength $dma_endpoints] != {width}}} {{write_checkpoint -force dma-cdc-debug.dcp; error "Missing DMA CDC {src}: source=[llength $dma_sources] sink=[llength $dma_endpoints]"}}',
            'set dma_timed_sync [concat $dma_timed_sync $dma_endpoints]',
            'set_max_delay -datapath_only 8 -from $dma_sources -to $dma_endpoints',
            'set_bus_skew 8 -from $dma_sources -to $dma_endpoints',
            f'puts "DMA_CDC_CHECK {src} {width} {width}"']
    lines += ['if {[llength $dma_timed_sync] != '+str(total)+'} {error "Incomplete DMA timed first stages"}',
        'set first_sync_false {}',
        'foreach cell $first_sync {if {[lsearch -exact $dma_timed_sync $cell]<0} {lappend first_sync_false $cell}}',
        'set_false_path -to [get_pins -of_objects $first_sync_false -filter {REF_PIN_NAME == D}]']
    return '\n'.join(lines)
