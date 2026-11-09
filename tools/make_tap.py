# Write a patched copy of the tape: patches the main CODE block (24000, 41400
# bytes) in place and recomputes its checksum. Refuses if any original byte
# differs from what the manifest expects.
#   python3 tools/make_tap.py original/HARD128.TAP original/HARD128-p01-p03.TAP p01 p02 p03
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'patches'))
from manifest import PATCHES

LOAD, LENGTH = 24000, 41400

def blocks(tap):
    i = 0
    while i < len(tap):
        n = tap[i] | tap[i + 1] << 8
        yield i + 2, n
        i += 2 + n

def main(src, dst, names):
    tap = bytearray(open(src, 'rb').read())
    header_seen = False; data_at = None
    for start, n in blocks(tap):
        flag = tap[start]
        if flag == 0 and n == 19 and tap[start + 1] == 3:
            length = tap[start + 12] | tap[start + 13] << 8
            param1 = tap[start + 14] | tap[start + 15] << 8
            header_seen = (length, param1) == (LENGTH, LOAD)
        elif flag == 0xFF and header_seen and n == LENGTH + 2:
            data_at = start + 1; break
        else:
            header_seen = False
    if data_at is None:
        raise SystemExit('main CODE block (24000, 41400) not found')
    byname = {p['name']: p for p in PATCHES}
    for name in names:
        for addr, orig, new in byname[name]['chunks']:
            off = data_at + addr - LOAD
            if not (LOAD <= addr and addr + len(new) <= LOAD + LENGTH):
                raise SystemExit(f'{name}: {addr:04X} is outside the main block')
            have = bytes(tap[off:off + len(orig)])
            if have != orig:
                raise SystemExit(f'{name}: tape has {have.hex()} at {addr:04X}, expected {orig.hex()}')
            tap[off:off + len(new)] = new
    chk = 0
    for b in tap[data_at - 1:data_at + LENGTH]:
        chk ^= b
    tap[data_at + LENGTH] = chk
    open(dst, 'wb').write(tap)
    print(f'wrote {dst} ({len(tap)} bytes) with {" ".join(names)}')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
