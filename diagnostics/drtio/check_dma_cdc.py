#!/usr/bin/env python3
"""Check every DMA CDC first-stage routed endpoint; LGPL-3.0-or-later.

Read-only implementation check: opens a DCP, never opens hardware/JTAG.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('build',type=Path);a=p.parse_args();build=a.build.resolve()
    # A failed recheck must not leave a previous PASS beside its new log.
    (build/'dma-cdc-results.json').unlink(missing_ok=True)
    groups=json.loads((build/'cdc-manifest.json').read_text())['dma_crossings']
    if len(groups)!=6 or sum(g['bits'] for g in groups)!=164:
        raise ValueError('Expected six complete DMA CDC groups/164 bits')
    dcp=build/'top_route.dcp'
    if not dcp.is_file() or any(c in str(dcp) for c in '{}\n'):
        raise ValueError('Missing/invalid routed checkpoint')
    lines=['set_param general.maxThreads 2',f'open_checkpoint {{{dcp}}}',
           'set report [open dma_cdc_endpoints.tsv w]',
           'puts $report "source\tendpoint\trequirement_ns\tslack_ns"']
    for g in groups:
        src,dst,width=g['source'],g['first_stage'],g['bits']
        if not all(re.fullmatch(r'\w+',n) for n in (src,dst)):
            raise ValueError('Invalid HDL name')
        lines += [
            f'set sources [get_cells -hierarchical -filter {{NAME =~ {src}_reg* && REF_NAME =~ FD*}}]',
            f'set endpoints [get_cells -hierarchical -filter {{NAME =~ {dst}_reg* && REF_NAME =~ FD*}}]',
            f'if {{[llength $sources] != {width} || [llength $endpoints] != {width}}} {{error "Incomplete routed DMA CDC: {src}"}}',
            'foreach endpoint $endpoints {',
            ' set paths [get_timing_paths -from $sources -to $endpoint -max_paths 1 -nworst 1]',
            ' if {[llength $paths] != 1} {error "Missing/false-pathed DMA endpoint: $endpoint"}',
            ' set requirement [get_property REQUIREMENT $paths]',
            ' set slack [get_property SLACK $paths]',
            ' if {![string is double -strict $requirement] || ![string is double -strict $slack]} {error "Missing/false-pathed DMA endpoint: $endpoint nonnumeric timing"}',
            ' if {abs($requirement-8.0)>0.001 || $slack<0} {error "DMA CDC delay failed: $endpoint requirement=$requirement slack=$slack"}',
            f' puts $report "{src}\t$endpoint\t$requirement\t$slack"',
            '}',
            f'report_timing -from $sources -to $endpoints -max_paths {width} -file dma_cdc_{src}.rpt']
    lines += ['close $report','report_exceptions -coverage -file dma_cdc_exceptions.rpt',
              'puts "DMA_ROUTED_ENDPOINTS_PASS 164"','close_design']
    script=build/'check_dma_cdc.tcl';script.write_text('\n'.join(lines)+'\n')
    with (build/'check_dma_cdc.log').open('w') as log:
        subprocess.run(['vivado','-mode','batch','-source',str(script)],cwd=build,
                       stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    log=(build/'check_dma_cdc.log').read_text()
    if not re.search(r'^DMA_ROUTED_ENDPOINTS_PASS 164$',log,re.M):
        raise ValueError('Vivado did not qualify all routed endpoints')
    rows=(build/'dma_cdc_endpoints.tsv').read_text().splitlines()
    if len(rows)!=165:raise ValueError('Missing routed endpoint evidence')
    result={'kind':'ROUTED_IMPLEMENTATION_NOT_HARDWARE','status':'PASS',
            'groups':6,'endpoints':164,'requirement_ns':8,
            'minimum_slack_ns':min(float(row.split('\t')[3]) for row in rows[1:]),
            'sha256':{name:hashlib.sha256((build/name).read_bytes()).hexdigest()
                for name in ('top_route.dcp','top.v','csr-map.json','cdc-manifest.json','dma_cdc_endpoints.tsv')}}
    (build/'dma-cdc-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
