# Whole-game A/B check: run the original and a patched game from the same race
# start, with the same keys held on each GAME frame (the game reads the keyboard
# once per main-loop pass at $9E34), and compare memory after every frame.
# Also reports T-states per game frame for both, i.e. the speed-up.
#   python3 tools/abtest.py FRAMES p01 [p02 ...]     (names from patches/manifest.py)
import sys, os, statistics
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'patches'))
from manifest import PATCHES
from hddrive import Drive, KEYMAP
from skoolkit.simutils import PC, T, SP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNA = f'{ROOT}/original/hd_loaded.z80'
LOOP = 0x9E34          # race main loop
SYNC = 0xDC37          # buffer-to-screen copy: every rendered frame, race and replay

def to_race(d):
    """Menus: SPACE, 1 keyboard, L drive on left, SPACE, then wait for the
    'turn key' screen. Each press is held until the screen changes."""
    def press(k, maxs=4):
        before = d.last_scr[:4096]; n = 0
        while d.last_scr[:4096] == before and n < maxs * 10:
            d.secs(0.1, k); n += 1
        d.secs(0.1)
    def settle(maxs=6):
        prev = None; t = 0
        while t < maxs:
            d.secs(0.5); t += 0.5
            if d.last_scr == prev: break
            prev = d.last_scr
    d.secs(4)
    for k in [' ', '1', 'L', ' ']:
        press(k); settle()
    d.secs(12)          # transmission choice counts down, then the race screen
    d.secs(0.5, 'Q')    # Q turns the key

DRIVE = [(60, 'Q'), (20, 'QO'), (20, 'QP'), (10, 'A'), (20, 'QP'), (40, 'Q'),
         (15, 'QO'), (30, 'Q'), (25, 'QP'), (10, ''), (20, 'A'), (30, 'Q'),
         (12, 'QOW'), (25, 'QS'), (40, 'QO'), (20, 'Q ')]

def keys_for(frame):
    """A fixed drive, repeated: accelerate, steer both ways, brake, coast,
    gear keys, SPACE (centre steering), long turns that leave the road."""
    total = sum(n for n, k in DRIVE)
    f = frame % total
    for n, k in DRIVE:
        if f < n: return k
        f -= n

def step_frame(d, keys):
    kb = [0] * 8
    for k in keys:
        i, b = KEYMAP[k]; kb[i] |= b
    d.tr.keyboard = kb
    r = d.sim.registers; t0 = r[T]
    # leave SYNC, then run to it again: exactly one rendered frame
    d.sim.trace(d.pc, -1, 1, 0, True, d._draw, None, kb, None, None); d.pc = r[PC]
    d.sim.trace(d.pc, SYNC, 0, r[T] + 30_000_000, True, d._draw, None, kb, None, None); d.pc = r[PC]
    if d.pc != SYNC:
        return None           # no 3D frame for 30M T-states: left the race
    return r[T] - t0

def bank_of(m, addr):
    return m.banks[0] if addr >= 0xC000 else (m.banks[2] if addr >= 0x8000 else m.banks[5])

def apply(d, patches):
    """patches: list of manifest entries. Refuses if the original bytes differ."""
    m = d.sim.memory
    for p in patches:
        for addr, orig, new in p['chunks']:
            bank = bank_of(m, addr); off = addr & 0x3FFF
            have = bytes(bank[off:off + len(orig)])
            if have != orig:
                raise SystemExit(f"{p['name']}: bytes at {addr:04X} are {have.hex()}, expected {orig.hex()}")
            bank[off:off + len(new)] = new

def run(frames, patches, compare=True, verbose=True):
    a = Drive(SNA); b = Drive(SNA)
    for d in (a, b):
        to_race(d)
        d.sim.trace(d.pc, SYNC, 0, d.sim.registers[T] + 30_000_000, True, d._draw, None, [0]*8, None, None)
        d.pc = d.sim.registers[PC]
    apply(b, patches)
    skip = set()
    for p in patches:
        for addr, orig, new in p['chunks']:
            skip.update(range(addr, addr + len(new)))
        for lo, hi in p['ignore']:
            skip.update(range(lo, hi + 1))
    ta, tb = [], []; first_bad = None
    for f in range(frames):
        k = keys_for(f)
        xa, xb = step_frame(a, k), step_frame(b, k)
        if xa is None or xb is None:
            if (xa is None) != (xb is None) and first_bad is None:
                first_bad = (f, 'one game left the 3D view and the other did not')
            break
        ta.append(xa); tb.append(xb)
        if compare:
            ma, mb = a.sim.memory, b.sim.memory
            for bank in range(8):
                xa, xb = ma.banks[bank], mb.banks[bank]
                if xa != xb:
                    base = {5: 0x4000, 2: 0x8000, 0: 0xC000}.get(bank, 0xC000)
                    diffs = [i for i in range(16384) if xa[i] != xb[i]
                             and not (bank == 0 and 0xC000 + i in skip)
                             and not (bank in (2, 5) and base + i in skip)]
                    # ignore dead stack bytes below SP (scratch the patch may write)
                    sp = a.sim.registers[SP]
                    diffs = [i for i in diffs if not (bank == 0 and 0xFE00 <= 0xC000 + i < sp)]
                    if diffs and first_bad is None:
                        first_bad = (f, bank, [hex(base + i) for i in diffs[:8]], len(diffs))
            if a.sim.registers[SP] != b.sim.registers[SP] and first_bad is None:
                first_bad = (f, 'SP', a.sim.registers[SP], b.sim.registers[SP])
        if first_bad: break
    return ta, tb, first_bad, a, b

if __name__ == '__main__':
    frames = int(sys.argv[1])
    byname = {p['name']: p for p in PATCHES}
    patches = [byname[n] for n in sys.argv[2:]]
    ta, tb, bad, a, b = run(frames, patches)
    print(f'frames run: {len(ta)}')
    print(f'original: {statistics.mean(ta):10.0f} T/frame  ({3546900/statistics.mean(ta):.2f} fps)')
    print(f'patched : {statistics.mean(tb):10.0f} T/frame  ({3546900/statistics.mean(tb):.2f} fps)')
    print(f'saving  : {100*(1-sum(tb)/sum(ta)):.1f}%')
    print('IDENTICAL memory every frame' if not bad else f'DIFFERENCE: {bad}')
    a.png(f'{ROOT}/original/ab_orig.png'); b.png(f'{ROOT}/original/ab_patch.png')
    sys.exit(1 if bad else 0)
