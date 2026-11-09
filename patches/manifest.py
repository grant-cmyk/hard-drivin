# The patch set. Each patch: name, what it changes, and chunks of
# (address, original bytes, new bytes). Addresses at $C000+ are RAM bank 0,
# $8000-$BFFF bank 2, $4000-$7FFF bank 5 - where the game's tape loads them.
# 'ignore' lists bytes that legitimately differ at run time (code the game
# rewrites itself), which the A/B memory check must not count.
import os
HERE = os.path.dirname(os.path.abspath(__file__))

def binfile(name):
    return open(os.path.join(HERE, name), 'rb').read()

ORIG_D77D = bytes.fromhex(
    '7d6c2600a7ed52d23cd71917ed6aa7ed52d23cd71917ed6aed5230011917ed6aed5230011917'
    'ed6aed5230011917ed6aed5230011917ed6aed5230011917ed6aed5230011917ed6aed523001'
    '1917')
ORIG_D743 = bytes.fromhex('d5eb6ffe803f3e00de0067cdba91a7ed5ad1c9')

PATCHES = [
    dict(name='p01', title='Divide: skip the whole-number steps when the answer is under 1',
         chunks=[(0xD77D, ORIG_D77D, binfile('p01.bin'))], ignore=[]),
    dict(name='p02', title='Sign-extend in 8 T-states instead of 29 ($D743)',
         chunks=[(0xD743, ORIG_D743, binfile('p02.bin'))], ignore=[]),
    dict(name='p03', title='Shift stub at $91BA returns straight after its shifts',
         chunks=[(0xD76D, b'\x00', b'\xc9'), (0xA0FC, b'\x00', b'\xc9')],
         ignore=[(0x91BA, 0x91BF)]),
]
