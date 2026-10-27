"""Scoped linked-flow audit; abstract callbacks remain unqualified. LGPL-3.0-or-later."""
import re
import struct
from package_local_candidate import loads


def check(data, symbols_text, disassembly, shape="legacy-v1"):
    if shape not in ("legacy-v1", "word-v2", "final-msr-v3"):
        raise ValueError("unknown compiler shape")
    machine, entry, segments = loads(data)
    if machine != 189 or entry != 0xffdc0050:
        raise ValueError('expected full PMU ELF')
    symbols = {}
    for line in symbols_text.splitlines():
        m = re.fullmatch(r'([0-9a-f]+) (?:([0-9a-f]+) )?([A-Za-z?]) (\S+)', line)
        if m:
            symbols[m[4]] = (int(m[1], 16), int(m[2], 16) if m[2] else 0)
    for forbidden in ('artiq_pmu_guard', 'artiq_pmu_enter_lab_guard'):
        if forbidden in symbols:
            raise ValueError('historical guard present')
    rows = {}
    for line in disassembly.splitlines():
        m = re.fullmatch(r'\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)', line)
        if m:
            rows[int(m[1], 16)] = (int(m[2], 16), m[3])

    def body(name):
        if name not in symbols:
            raise ValueError('missing ' + name)
        start, size = symbols[name]
        if not size or size % 4:
            raise ValueError('bad symbol size')
        result = []
        for pc in range(start, start + size, 4):
            if pc not in rows:
                raise ValueError('missing instruction')
            segments_here = [s for s in segments if s['address'] <= pc and pc + 4 <= s['address'] + s['filesz']]
            if len(segments_here) != 1:
                raise ValueError('instruction outside unique ELF payload')
            s = segments_here[0]
            word = struct.unpack_from('<I', s['payload'], pc - s['address'])[0]
            if rows[pc][0] != word:
                raise ValueError('disassembly differs from ELF')
            result.append((pc, word, rows[pc][1].split()[0]))
        return result

    terminal = body('pit_terminal_audit')
    if [w for _, w, _ in terminal] != [0xb8220004, 0xba020004, 0xb800fffc]:
        raise ValueError('terminal is not barrier/sleep/backbranch')
    termaddr = symbols['pit_terminal_audit'][0]
    adapteraddr = symbols['terminal_adapter'][0]
    memsetaddr = symbols.get('memset', (-1, 0))[0]

    def relative(pc, word):
        offset = word & 0xffff
        previous = rows.get(pc - 4, (0, ''))[0]
        if previous >> 16 == 0xb000:
            offset |= (previous & 0xffff) << 16
            return pc + (offset - (1 << 32) if offset & (1 << 31) else offset)
        return pc + (offset - 65536 if offset & 32768 else offset)

    adapter = body('terminal_adapter')
    if len(adapter) != 4 or [w for _, w, _ in adapter[:2]] != [0x3021fffc, 0xf9e10000] or adapter[2][1] >> 16 != 0xb9f4 or relative(*adapter[2][:2]) != termaddr or adapter[3][1] != 0x80000000:
        raise ValueError('adapter must call exact terminal without return')
    profile = body('pit_profile_entry_audit')
    start = profile[0][0]; end = start + len(profile) * 4
    ordinary = {'addik', 'swi', 'lwi', 'pcmpeq', 'or', 'addk', 'andi', 'xor', 'imm', 'bslli', 'lw', 'sw'}
    conditional = {'beqid', 'bneid', 'beqi', 'bnei'}
    calls = []; indirect = []; branches = 0
    for index, (pc, word, mnemonic) in enumerate(profile):
        if mnemonic in ordinary:
            # Refuse known control opcodes disguised as ordinary disassembly.
            if word >> 24 in (0x98, 0xb6, 0xb8, 0xb9, 0xba, 0xbc, 0xbe, 0x99):
                raise ValueError('hidden control opcode')
            continue
        if mnemonic == 'brald':
            if word & 0xffff07ff != 0x99fc0000:
                raise ValueError('unexpected indirect call encoding')
            register = (word >> 11) & 31
            allowed_registers = {"legacy-v1": (22,24,27,28,29), "word-v2": (22,25,26,28,29), "final-msr-v3": (22,24,26,27,29)}
            if register not in allowed_registers[shape]:
                raise ValueError('unreviewed callback register')
            indirect.append(register)
        elif mnemonic == 'brlid':
            if word >> 16 != 0xb9f4:
                raise ValueError('unexpected direct call encoding')
            calls.append((pc, relative(pc, word)))
        elif mnemonic in conditional or mnemonic in ('brid', 'bri'):
            if word >> 24 not in (0xbc, 0xbe, 0xb8):
                raise ValueError('unexpected branch encoding')
            target = relative(pc, word)
            if not start <= target < end or target % 4:
                raise ValueError('branch escapes entry')
            branches += 1
        else:
            raise ValueError('unreviewed instruction/return: ' + mnemonic)
        if mnemonic.endswith('d') and (index + 1 >= len(profile) or profile[index + 1][2] not in ordinary):
            raise ValueError('unexpected delay slot')
    expected_calls = [adapteraddr, memsetaddr, termaddr] + ([memsetaddr] if shape == "legacy-v1" else [])
    if sorted(target for _, target in calls) != sorted(expected_calls):
        raise ValueError('wrong direct call targets/counts')
    expected_indirect = [22, 29, 22, 27, 24, 28, 28, 24, 24] if shape == "legacy-v1" else [22, 29, 22, 28, 25, 26, 26, 25, 25]
    if shape == "final-msr-v3":
        expected_indirect = [24,22,24,29,26,27,26,27,26,24]
    if sorted(indirect) != sorted(expected_indirect):
        raise ValueError('unexpected abstract callback inventory')
    if shape == "final-msr-v3":
        # Exact compiler tail: MSR callback, error test, load+compare, error
        # test, pass status, branch to adapter; rejected-entry fallback follows.
        expected_tail = [0x10b30000,0x99fcc000,0x30c10078,0xbe23fe70,
                         0xe8610078,0xe881007c,0x88632000,0xbe23fe60,
                         0x10d60000,0xb800fe60,0xb9f4fd58,0x80000000]
        if [word for _,word,_ in profile[-12:]] != expected_tail:
            raise ValueError('final MSR call/error/compare terminal block changed')
    if profile[-2][0] != calls[-1][0] or calls[-1][1] != termaddr:
        raise ValueError('entry may fall through instead of terminal')
    return {'status': 'SCOPED_PROFILE_LINKED_FLOW_PASS_NOT_HARDWARE',
            'hardware_executed': False, 'deployable': False,
            'physical_backend_ready': False, 'destructive_test_allowed': False,
            'compiler_shape': shape, 'internal_branches': branches, 'abstract_callback_sites': len(indirect),
            'limits': 'Static branch/call inventory only; callback identity/dataflow, liveness, MMIO, IRQ and visibility remain unproven'}
