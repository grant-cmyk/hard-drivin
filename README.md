# Hard Drivin' optimisation (ZX Spectrum 128K)

Classification: **Personal - private. Not for publishing or sharing.**

Domark's Hard Drivin' (Spectrum 128K version by Binary Design, 1989) is technically good but too slow to
play. This repo finds where its frame time goes and holds patches that speed it up while keeping its
behaviour the same. It follows the method of the Alien 8 optimisation workstream (`grant-cmyk/alien8`).

**The game itself is never committed.** `.gitignore` blocks tapes, snapshots and screens. Attach
`HardDrivin128.tap.zip` to a session and put it in `original/` (ignored).

## Layout

- `CONTINUE.md` - where things stand; read first.
- `PROJECT-LOG.md` - dated log.
- `tools/hddrive.py` - drives the game in SkoolKit 10.2's 128K simulator (contention on): hold keys, capture screens, sample the PC to profile.
- `tools/abtest.py` - original vs patched game, same keys per rendered frame, all memory compared every frame; prints the speed-up.
- `tools/profile.py` - exact T-states per routine (shadow call stack), per game frame.
- `tools/make_tap.py` - writes a patched copy of the tape (into `original/`, never committed).
- `patches/` - one `.asm` per patch (assemble with `pasmo x.asm x.bin`), `manifest.py` lists every patch with the original bytes it expects.
- `tests/` - unit A/B tests for single routines.
- `notes/` - memory map, routine notes, measurements (`profile-and-routines.md`).

## Setup (cloud session)

```bash
pip install skoolkit==10.2
```

```bash
tap2sna.py -c machine=128 original/HARD128.TAP original/hd_loaded.z80
```

```bash
python3 tools/abtest.py 1500 p01 p02 p03
```

```bash
python3 tools/make_tap.py original/HARD128.TAP original/HARD128-p01-p03.TAP p01 p02 p03
```
