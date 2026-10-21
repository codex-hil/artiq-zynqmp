#!/usr/bin/env python3
"""Recheck retained PS reconstruction/SDT input hashes; LGPL-3.0-or-later."""
import json
from pathlib import Path
from check_remote_rtio_build import sha


def tree(root,files):
    root=Path(root)
    for name,expected in files.items():
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe source input path')
        path=root/rel
        if path.resolve()!=root.resolve()/rel or not path.is_file():raise ValueError('Missing/linked source input: '+name)
        if sha(path)!=expected:raise ValueError('Changed source input: '+name)


def verify(path,expected):
    if sha(path)!=expected:raise ValueError('Changed source binding manifest')
    manifest=json.loads(path.read_text())
    for item in manifest['trees']:
        tree(item['root'],item['files'])
        if item.get('exact_file_set'):
            root=Path(item['root']);actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
            if actual!=set(item['files']):raise ValueError('Source tree file set changed')
    for item in manifest['equal_files']:
        a,b=Path(item['left']),Path(item['right'])
        if sha(a)!=item['sha256'] or sha(b)!=item['sha256']:raise ValueError('Source equivalence changed')
    return dict(status='RETAINED_PS_SDT_SOURCE_INPUTS_PASS',hardware_executed=False,
        binding_sha256=expected,trees_checked=len(manifest['trees']),equal_files_checked=len(manifest['equal_files']),
        scope='Current byte hashes bound to recorded reconstruction; does not rerun tools, prove historical causality or provide signed provenance.')
