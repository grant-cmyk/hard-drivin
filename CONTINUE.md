# CONTINUE - Hard Drivin' optimisation

**Stamped:** Mon 09 Nov 2026 21:20 SAST · cloud session (no machine name) · at commit `5ea9628`

**Status:** Active. Profiled; three output-identical patches (p01-p03) make the race **7.3% faster**
(memory identical every frame over a full race). A patched tape exists for a playtest; it is not a
release until Grant has played it.

**Waiting on Grant:**
1. Playtest `HARD128-p01-p03.TAP` (sent in the chat 9 Nov) and say whether it still plays the same.
2. Decide whether picture-changing speed-ups are allowed (see "An honest ceiling" in
   `notes/profile-and-routines.md`) - exact-only work likely tops out at ~25-30%.

**Next step (Claude):** p04, the object scan at `$9F0D` (~270 records a frame): keep camera X in a
register and skip records with POPs; prove with `tools/abtest.py 1500 p01 p02 p03 p04`.

**Needs from Grant each session:** attach `HardDrivin128.tap.zip` (it is never stored in the repo).

**Read:** `notes/profile-and-routines.md` (the profile, routine map, patch list, candidates),
`PROJECT-LOG.md`, `patches/manifest.py`, `tools/abtest.py`.
