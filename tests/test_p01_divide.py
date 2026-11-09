# A/B test of patch 01 (divide fast path) in isolation: run the original and
# the patched $D77D on the same inputs and compare every register and flag.
# Uses original/race64.bin, a 64K memory image taken during a race (never
# committed); it is made on first run from original/hd_loaded.z80.
#   python3 tests/test_p01_divide.py [REPO] [RANDOM_CASES] [PATCH_BIN]
import random, sys, os
from skoolkit.simulator import Simulator
from skoolkit.simutils import A, F, B, C, D, E, H, L, SP, PC, T

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
if not os.path.exists(f'{ROOT}/original/race64.bin'):
    sys.path.insert(0, f'{ROOT}/tools')
    import abtest
    from hddrive import Drive
    dr = Drive(abtest.SNA); abtest.to_race(dr)
    for _ in range(60): abtest.step_frame(dr, 'Q')
    mm = dr.sim.memory
    img = bytes(mm.memory[0]) + bytes(mm.banks[5]) + bytes(mm.banks[2]) + bytes(mm.banks[mm.o7ffd % 8])
    open(f'{ROOT}/original/race64.bin', 'wb').write(img)
mem0 = bytearray(open(f'{ROOT}/original/race64.bin', 'rb').read())
patch = open(sys.argv[3] if len(sys.argv) > 3 else f'{ROOT}/patches/p01.bin', 'rb').read()
mem1 = bytearray(mem0); mem1[0xD77D:0xD77D + len(patch)] = patch
STUB = 0x5B00                       # CALL $D77D / then stop at STUB+3
for m in (mem0, mem1):
    m[STUB:STUB + 3] = bytes([0xCD, 0x7D, 0xD7])

def run2(mem, *args):
    # robust stepping: one instruction at a time with the pure-Python simulator
    m = bytearray(mem)
    sim = Simulator(m, {}, {'fast_djnz': False, 'fast_ldir': False})
    r = sim.registers
    hl, de, a, f, a2, f2, bc = args
    r[H], r[L], r[D], r[E] = hl >> 8, hl & 255, de >> 8, de & 255
    r[A], r[F], r[B], r[C] = a, f, bc >> 8, bc & 255
    r[8], r[9] = a2, f2
    r[SP] = 0xFF00; r[T] = 0
    r[PC] = STUB
    for _ in range(3000):
        sim.run()
        if r[PC] in (STUB + 3, 0xD73C): break
    else:
        raise RuntimeError('did not return')
    keys = (A, F, B, C, D, E, H, L, 8, 9, SP, PC)
    return tuple(r[k] for k in keys), r[T]

random.seed(1)
cases = []
for de in [0, 1, 2, 127, 128, 255, 256, 257, 1000, 9025, 0x7FFF, 0x8000, 0xFFFF]:
    for hl in [0, 1, de - 1, de, de + 1, 255, 256, 0x7FFF, 0x8000, 0xFFFF, 3462]:
        cases.append((hl & 0xFFFF, de))
for _ in range(int(sys.argv[2]) if len(sys.argv) > 2 else 20000):
    de = random.choice([random.randrange(1, 10000), random.randrange(0, 65536), random.randrange(1, 300)])
    hl = random.choice([random.randrange(0, de + 1) if de else 0, random.randrange(0, 4000), random.randrange(0, 65536)])
    cases.append((hl, de))
t0 = t1 = 0; bad = 0; fast = 0
for hl, de in cases:
    extra = (random.randrange(256), random.randrange(256), random.randrange(256), random.randrange(256), random.randrange(65536))
    o, ta = run2(mem0, hl, de, *extra)
    p, tb = run2(mem1, hl, de, *extra)
    t0 += ta; t1 += tb; fast += hl < de
    if o != p:
        bad += 1
        if bad < 10: print('MISMATCH hl=%04X de=%04X' % (hl, de), o, p)
print(f'{len(cases)} cases, {bad} mismatches, fast-path cases {fast}; T original {t0} patched {t1} ({100*(t0-t1)/t0:.1f}% less)')
sys.exit(1 if bad else 0)
