#!/usr/bin/env python3
"""Verified PS export copy/relocation and parameter comparison; LGPL-3.0-or-later."""
import argparse,json,shutil
from pathlib import Path
from check_remote_rtio_build import sha


def relative(name):
    p=Path(name)
    if not name or p.is_absolute() or '..' in p.parts or '\n' in name or '\r' in name:raise ValueError('Unsafe export path')
    return p


def verified(source):
    source=source.resolve();receipt=json.loads((source/'retrieval.json').read_text());files=receipt['sha256']
    for name,expected in files.items():
        rel=relative(name);p=source/rel
        if p.resolve()!=source/rel or not p.is_file() or sha(p)!=expected:raise ValueError('Missing/linked/changed export file: '+name)
    for name in ('mi_xci_files.txt','mi_part.txt','mi_bd_cells.txt'):
        if name not in files:raise ValueError('Unpinned importer index: '+name)
    return files


def references(source,origin,files):
    if not origin.startswith('/') or origin.endswith('/'):raise ValueError('Require absolute original export directory without trailing slash')
    refs=(source/'mi_xci_files.txt').read_text().splitlines();names=[]
    for ref in refs:
        if not ref.startswith(origin+'/'):raise ValueError('External exported IP reference')
        name=ref[len(origin)+1:];relative(name)
        if name not in files or not name.endswith('.xci'):raise ValueError('Missing exported IP')
        names.append(name)
    if not names or len(set(names))!=len(names):raise ValueError('Missing/duplicate IP references')
    return names


def compare_exports(source,baseline,names):
    differences={}
    for name in names:
        a=json.loads((source/name).read_text())['ip_inst']['parameters'];b=json.loads((baseline/name).read_text())['ip_inst']['parameters']
        for category in sorted(a.keys()|b.keys()):
            av={k:[v['value'] for v in values] for k,values in a.get(category,{}).items()}
            bv={k:[v['value'] for v in values] for k,values in b.get(category,{}).items()}
            changed={k:dict(new=av.get(k),baseline=bv.get(k)) for k in sorted(av.keys()|bv.keys()) if av.get(k)!=bv.get(k)}
            if changed:differences[name+':'+category]=changed
    report_names=['mi_part.txt','mi_bd_cells.txt']
    for cell in (source/'mi_bd_cells.txt').read_text().splitlines():
        relative(cell)
        report_names.extend(str(p.relative_to(source)) for p in (source/cell).glob('*.txt'))
    changed_reports=[n for n in report_names if not (baseline/n).is_file() or (source/n).read_bytes()!=(baseline/n).read_bytes()]
    return dict(status='PS_PARAMETERS_AND_REPORTS_IDENTICAL' if not differences and not changed_reports else 'PS_COMPARISON_DIFFERENCES',parameter_differences=differences,changed_reports=changed_reports)


def prepare(source,origin,output,baseline=None):
    source=source.resolve();output=output.resolve()
    if output.exists():raise ValueError('Use a fresh importer directory')
    files=verified(source);names=references(source,origin,files)
    report=dict(status='IMPORT_VIEW_PREPARED_NOT_HARDWARE',hardware_executed=False,source=str(source),original_root=origin,output=str(output),receipt_sha256=sha(source/'retrieval.json'),files_verified=len(files))
    if baseline is not None:
        report['comparison']=compare_exports(source,baseline.resolve(),names)
        if report['comparison']['status']!='PS_PARAMETERS_AND_REPORTS_IDENTICAL':
            raise ValueError('PS export differs from selected baseline: '+json.dumps(report['comparison']))
    if any(p.is_symlink() for p in source.rglob('*')):raise ValueError('Linked export content')
    output.mkdir(parents=True)
    for name in files:
        dest=output/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,dest)
        if sha(dest)!=files[name]:raise ValueError('Copied export hash mismatch')
    before=(output/'mi_xci_files.txt').read_text();after=''.join(str(output/name)+'\n' for name in names)
    (output/'mi_xci_files.txt').write_text(after)
    report['relocation']=dict(before=before,after=after)
    (output/'import-view.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--export',required=True,type=Path);p.add_argument('--original-root',required=True);p.add_argument('--output',required=True,type=Path);p.add_argument('--baseline',type=Path);a=p.parse_args()
    print(json.dumps(prepare(a.export,a.original_root,a.output,a.baseline),indent=2))

if __name__=='__main__':main()
