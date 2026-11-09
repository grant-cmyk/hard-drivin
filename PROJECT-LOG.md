# Project log

- **2026-11-09 19:14-19:45 SAST** (cloud session) - Workstream opened at Grant's request ("very very slow to the point of being unplayable ... look at ways to optimize it"). Grant: personal only, not for publishing or sharing.
  - Tried the `zx` 48K emulator: the tape needs 128K (reset).
  - Installed SkoolKit 10.2; `tap2sna.py -c machine=128` loads the tape; `trace.py` runs it to the title screen.
  - Wrote `tools/hddrive.py`, which runs frame by frame with contention and captures screens. SPACE moves from the credits to the controls menu, but "1" does not select keyboard: keys set through `simulator.trace(..., keyboard, ...)` do not seem to register. **Lead:** use the simulator's `press_keys` / `press` as `skoolkit/kbtracer.py` does.
  - Sampled PCs during the menu sit around C59F-C5A2 in bank 3, where the bytes look like data (music?). Not yet explained; check the bank mapping in the C simulator before trusting any disassembly.
  - Notion row: https://app.notion.com/p/41342c9abb3281378950f9d44197a22c
- **2026-11-09 20:56-21:20 SAST** (cloud session, signed in as grant@ttro.com; Personal work, filed in the Personal repo) - profiled the race and shipped the first three output-identical patches.
  - **Keys were never broken.** The menus need a key held until the screen changes; the earlier "1 does not register" was timing. `tools/abtest.py` `to_race()` now drives the menus reliably.
  - **Controls read from the code:** Q accelerate / turn key, A brake, O / P steer, W / S gears, SPACE centre, 0 abort replay.
  - **The C59F-C5A2 mystery:** it is code, not data - a key-wait and delay loop at `$C594` in RAM bank 0.
  - **Measured:** interrupts are off for the whole race; one game frame (main loop `$9E34`) costs 0.7-1.2M T-states, **3-5 frames a second**; the 3D render `$9EA9` is ~88%. The perspective divide `$D77D` alone is ~21%. Full table: `notes/profile-and-routines.md`.
  - **Tried and ruled out:** dropping the divide's fraction bits - the clipper reads them (`$DA6A`), so the picture would change.
  - **Patches p01-p03** (`patches/`, listed in `patches/manifest.py`): divide fast path (~8%), faster sign-extend in `$D743` (~0.5%), RET-first shift stub (~0.4%). **Together 7.3% over a complete race to GAME OVER (629 rendered frames, off-road, crash, instant replay), memory identical after every frame.** Negative controls fail as they should.
  - **New tools:** `tools/abtest.py` (whole-game A/B), `tools/profile.py` (exact per-routine cost), `tools/make_tap.py` (patched tape), `tests/test_p01_divide.py`.
  - **Patched tape for a playtest:** `original/HARD128-p01-p03.TAP` (not committed - the game never is). Sent to Grant in the chat for playtesting; not a release until he has played it.
  - **Honest ceiling noted:** output-identical work likely tops out ~25-30%; more needs Grant's decision on picture-changing options.
