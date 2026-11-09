# CONTINUE - Hard Drivin' optimisation

**Stamped:** Mon 09 Nov 2026 19:45 SAST · cloud session (no machine name) · initial commit, not yet pushed

**Status:** set-up. The game runs in a 128K simulator to its controls menu. No timing profile yet, so no optimisation claims yet.

**Next step (Claude):** get keypresses working (SkoolKit `press_keys`), choose keyboard, start a race, then sample the PC for ~10 s of driving to find the routines that use the frame time (likely 3D transform maths, line/polygon drawing, screen buffer copy - unverified).

**Needs from Grant each session:** attach `HardDrivin128.tap.zip` (it is never stored in the repo).

**Read:** `PROJECT-LOG.md`, `notes/tape-and-memory.md`, `tools/hddrive.py`.
