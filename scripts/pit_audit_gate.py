"""Read-only source/artifact audit gate. No hardware execute path. LGPL-3.0-or-later."""
import argparse
import hashlib
import json
from pathlib import Path
from check_pit_profile_flow import check as check_flow
from check_pit_word_stores import check as check_word_stores
from check_pmu_boundary_image import check as check_layout

PROFILE = 'pit-counter-before-sleep-word-audit-v2'
SOURCES = {'diagnostics/ddr/pit_collect/' + name + suffix for name, suffix in [
    ('pit_collect', '.c'), ('pit_collect', '.h'), ('pit_publish', '.c'), ('pit_publish', '.h'),
    ('pit_capture', '.c'), ('pit_capture', '.h'), ('pit_sleep_model', '.c'),
    ('pit_sleep_model', '.h'), ('pit_terminal_audit', '.c'), ('pit_profile_audit', '.c')]}
SCRIPTS = {'scripts/' + name + '.py' for name in [
    'pit_audit_gate', 'check_pit_profile_flow', 'check_pmu_boundary_image',
    'package_local_candidate', 'build_pmu_boundary', 'stage_pmu_boundary', 'check_pit_word_stores']}


def _read_pinned(path, digest):
    if type(digest) is not str or len(digest) != 64:
        raise ValueError('invalid digest')
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('changed pinned input: ' + str(path))
    return data


def audit(manifest, repo):
    required = {'schema', 'profile', 'deployable', 'hardware_executed',
                'source_sha256', 'script_sha256', 'artifacts'}
    if type(manifest) is not dict or set(manifest) != required:
        raise ValueError('exact audit manifest fields required')
    if type(manifest['schema']) is not int or manifest['schema'] != 1 or manifest['profile'] != PROFILE:
        raise ValueError('unsupported audit profile/schema')
    if manifest['deployable'] is not False or manifest['hardware_executed'] is not False:
        raise ValueError('audit profile cannot claim deployment/hardware')
    for key, names in [('source_sha256', SOURCES), ('script_sha256', SCRIPTS)]:
        pins = manifest[key]
        if type(pins) is not dict or set(pins) != names:
            raise ValueError('exact source/helper closure required')
        for name, digest in pins.items():
            _read_pinned(Path(repo) / name, digest)
    artifacts = manifest['artifacts']
    if type(artifacts) is not dict or set(artifacts) != {'elf', 'symbols', 'disassembly'}:
        raise ValueError('exact ELF/symbol/disassembly pins required')
    loaded = {}
    for key, item in artifacts.items():
        if type(item) is not dict or set(item) != {'path', 'sha256'}:
            raise ValueError('exact artifact pin fields required')
        loaded[key] = _read_pinned(item['path'], item['sha256'])
    # Hash and check the same bytes, not a second mutable-file read.
    symbols = loaded['symbols'].decode('utf-8')
    layout = check_layout(loaded['elf'], symbols)
    flow = check_flow(loaded['elf'], symbols, loaded['disassembly'].decode('utf-8'), shape='word-v2')
    word_stores = check_word_stores(loaded['elf'], symbols)
    return {'status': 'PINNED_OFFLINE_AUDIT_PASS_NOT_DEPLOYMENT',
            'hardware_executed': False, 'deployable': False,
            'physical_backend_ready': False, 'destructive_test_allowed': False,
            'layout': layout, 'flow': flow, 'word_stores': word_stores,
            'limits': 'Content consistency only, not trusted provenance, reproducible build or permission to access hardware'}


def require_deployment(*args, **kwargs):
    raise ValueError('PIT audit profile is never deployable: no qualified MMIO recovery, visibility or runtime hook')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads(args.manifest.read_text()), Path(__file__).resolve().parents[1]), indent=2))
