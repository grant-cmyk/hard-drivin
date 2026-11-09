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
- `notes/` - memory map, routine notes, measurements.

## Setup (cloud session)

```bash
pip install skoolkit==10.2
tap2sna.py -c machine=128 original/HARD128.TAP original/hd_loaded.z80
```
