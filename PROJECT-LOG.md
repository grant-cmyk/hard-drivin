# Project log

- **2026-11-09 19:14-19:45 SAST** (cloud session) - Workstream opened at Grant's request ("very very slow to the point of being unplayable ... look at ways to optimize it"). Grant: personal only, not for publishing or sharing.
  - Tried the `zx` 48K emulator: the tape needs 128K (reset).
  - Installed SkoolKit 10.2; `tap2sna.py -c machine=128` loads the tape; `trace.py` runs it to the title screen.
  - Wrote `tools/hddrive.py`, which runs frame by frame with contention and captures screens. SPACE moves from the credits to the controls menu, but "1" does not select keyboard: keys set through `simulator.trace(..., keyboard, ...)` do not seem to register. **Lead:** use the simulator's `press_keys` / `press` as `skoolkit/kbtracer.py` does.
  - Sampled PCs during the menu sit around C59F-C5A2 in bank 3, where the bytes look like data (music?). Not yet explained; check the bank mapping in the C simulator before trusting any disassembly.
  - Notion row: https://app.notion.com/p/41342c9abb3281378950f9d44197a22c
