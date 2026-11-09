# Drive Hard Drivin' 128 in SkoolKit's simulator (contention on): hold keys,
# capture screens, and sample the PC to profile where the time goes.
import sys, io, contextlib, collections, numpy as np
from PIL import Image
from skoolkit import CCMIOSimulator
from skoolkit.cmiosimulator import CMIOSimulator
from skoolkit.snapshot import Snapshot
from skoolkit.simutils import from_snapshot, PC, T
from skoolkit.trace import Tracer

KEYMAP = {}
rows = ['^ZXCV', 'ASDFG', 'QWERT', '12345', '09876', 'POIUY', '\nLKJH', ' $MNB']  # ^=CAPS $=SYM
for i, r in enumerate(rows):
    for b, k in enumerate(r): KEYMAP[k] = (i, 1 << b)
FRAME = 70908

class Drive:
    def __init__(self, sna):
        s = Snapshot.get(sna)
        cls = CCMIOSimulator or CMIOSimulator
        self.sim = from_snapshot(cls, s, {}, {'ay': [None]*16}, {'fast_djnz': False, 'fast_ldir': False}, None)
        self.sim.memory.out7ffd(s.out7ffd)
        self.tr = Tracer(self.sim, s.border, s.out7ffd, s.outfffd, list(s.ay), s.outfe, True)
        self.sim.set_tracer(self.tr)
        self.pc = s.pc
        self.held = set()
        self.last_scr = None
        self.frames = 0
    def _draw(self, scr, frame, border, kb):
        self.last_scr = bytes(scr); self.frames += 1
        return True
    def run(self, tstates, keys=''):
        kb = [0] * 8
        for k in keys:
            i, b = KEYMAP[k]; kb[i] |= b
        self.held = set(keys)
        self.tr.keyboard = kb
        regs = self.sim.registers
        self.sim.trace(self.pc, -1, 0, regs[T] + tstates, True, self._draw, None, kb, None, None)
        self.pc = regs[PC]
    def secs(self, s, keys=''):
        for _ in range(int(s * 50)): self.run(FRAME, keys)
    def bank_of(self, pc):
        if pc < 0x4000: return 'ROM'
        if pc < 0x8000: return '5'
        if pc < 0xC000: return '2'
        return str(self.tr.out7ffd & 7)
    def profile(self, s, keys='', step=1013):
        h = collections.Counter(); n = int(s * 3546900 / step)
        for _ in range(n):
            self.run(step, keys); h[(self.bank_of(self.pc), self.pc)] += 1
        return h, n
    def png(self, name):
        d = self.last_scr
        pal = [(0,0,0),(0,0,215),(215,0,0),(215,0,215),(0,215,0),(0,215,215),(215,215,0),(215,215,215)]
        palb = [(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)]
        img = np.zeros((192,256,3),np.uint8)
        for y in range(192):
            a = ((y&7)<<8)|((y&0x38)<<2)|((y&0xC0)<<5)
            for cx in range(32):
                b = d[a+cx]; at = d[6144+(y>>3)*32+cx]; p = palb if at&64 else pal
                for bit in range(8):
                    img[y, cx*8+bit] = p[at&7] if b & (128>>bit) else p[(at>>3)&7]
        Image.fromarray(img).resize((512,384),Image.NEAREST).save(name)
