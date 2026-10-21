"""Fixed known-board volatile identities and lease scope. LGPL-3.0-or-later."""
BOARDS={
 'KASLI04':dict(dna=0x006c440674704854,mac='02:4b:04:70:48:54',link_local='fe80::4b:4ff:fe70:4854'),
 'KASLI01':dict(dna=0x007865085f704854,mac='02:4b:01:48:48:54',link_local='fe80::4b:1ff:fe48:4854'),
 'KASLI03':dict(dna=0x0048458a64b04854,mac='02:4b:03:48:48:54',link_local='fe80::4b:3ff:fe48:4854')}


def identity(board):
    if board not in BOARDS:raise ValueError('Unknown/unqualified board identity')
    return dict(BOARDS[board])


def locks(board,runtime=False):
    identity(board)
    names=['kasli-'+board] if board in ('KASLI01','KASLI04') else ['kasli-KASLI01','kasli-KASLI02','kasli-KASLI03']
    if runtime:names.append('genesys-210383B7F02DA')
    return sorted('/home/codex-hil/.cache/'+n+'.lock' for n in names)
