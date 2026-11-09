# Exact per-routine cost of the game, from a shadow call stack.
#   python3 tools/profile.py [FRAMES] [p01 p02 ...]
# Drives to a race (tools/abtest.py), holds Q for 60 game frames, then traces
# FRAMES main-loop passes one instruction at a time and prints inclusive and
# exclusive T-states per routine, calls per frame, and the call tree.
import sys, os, collections
sys.path.insert(0, os.path.dirname(__file__))
import abtest
from hddrive import Drive
from skoolkit.simutils import PC, T, SP

CALLOPS = {0xCD, 0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC}

def trace_frames(d, n_frames, start=abtest.LOOP):
    sim = d.sim; regs = sim.registers; mem = sim.memory
    sim.trace(d.pc, start, 0, regs[T] + 30_000_000, True, None, None, [0] * 8, None, None)
    d.pc = regs[PC]
    incl = collections.Counter(); excl = collections.Counter(); calls = collections.Counter()
    pcc = collections.Counter(); pcn = collections.Counter(); paths = collections.Counter()
    stack = [('ROOT', None, None)]

    def tf(pc, i, t0):
        npc = regs[PC]; sp = regs[SP]; dt = regs[T] - t0
        excl[stack[-1][0]] += dt; pcc[pc] += dt; pcn[pc] += 1
        seen = set()
        for f in stack:
            if f[0] not in seen:
                incl[f[0]] += dt; seen.add(f[0])
        path = tuple(f[0] for f in stack[1:6])
        for k in range(1, len(path) + 1):
            paths[path[:k]] += dt
        op = mem[pc]
        if op in CALLOPS:
            tgt = mem[(pc + 1) & 0xFFFF] | mem[(pc + 2) & 0xFFFF] << 8
            if npc == tgt and npc != ((pc + 3) & 0xFFFF):
                stack.append((tgt, (pc + 3) & 0xFFFF, sp)); calls[tgt] += 1
                return
        elif op & 0xC7 == 0xC7 and npc == op & 0x38:
            stack.append((npc, (pc + 1) & 0xFFFF, sp)); calls[npc] += 1
            return
        if len(stack) > 1 and stack[-1][1] == npc and sp == ((stack[-1][2] + 2) & 0xFFFF):
            stack.pop()

    t0 = regs[T]
    for _ in range(n_frames):
        sim.trace(d.pc, -1, 1, 0, True, None, None, d.tr.keyboard, lambda pc: '', tf)
        d.pc = regs[PC]
        sim.trace(d.pc, start, 0, 0, True, None, None, d.tr.keyboard, lambda pc: '', tf)
        d.pc = regs[PC]
    return dict(incl=incl, excl=excl, calls=calls, pcc=pcc, pcn=pcn, paths=paths,
                total=regs[T] - t0, frames=n_frames)

def report(r, top=30):
    total, n = r['total'], r['frames']
    print(f'{total / n:.0f} T-states per game frame ({3546900 * n / total:.2f} frames a second)')
    print(' routine   excl%   incl%  calls/frame')
    for k, v in r['excl'].most_common(top):
        if k == 'ROOT': continue
        print(f'  {k:04X}   {100 * v / total:5.1f}   {100 * r["incl"][k] / total:5.1f}   {r["calls"][k] / n:7.1f}')

if __name__ == '__main__':
    frames = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    from manifest import PATCHES
    byname = {p['name']: p for p in PATCHES}
    d = Drive(abtest.SNA); abtest.to_race(d)
    abtest.apply(d, [byname[x] for x in sys.argv[2:]])
    for f in range(60):
        abtest.step_frame(d, 'Q')
    kb = [0] * 8; i, b = abtest.KEYMAP['Q']; kb[i] |= b; d.tr.keyboard = kb
    report(trace_frames(d, frames))
