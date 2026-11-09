# Where the frame time goes (measured 9 Nov 2026)

Classification: **Personal - private.**

All figures are from SkoolKit 10.2's 128K simulator with memory contention, driving a race with
`tools/abtest.py` / `tools/profile.py`. They are T-states (the Z80 runs 3,546,900 a second; a TV
frame is 70,908).

## The headline

- **Interrupts are off for the whole race** (`DI`, IM 2 set up but never enabled). Every T-state
  is the game's own work; there is no frame sync and no music interrupt.
- **One game frame = one pass of the main loop at `$9E2F` → `$9E34`.** It costs **0.7-1.2 million
  T-states** depending on the scene: **3 to 5 frames a second**. With Q held on the opening
  straight it measured 1.19M T (16.8 TV frames, ~3 fps).
- **The 3D render `$9EA9` is ~88% of the frame.** The rest: screen copy `$DC37` ~6%, `$F910` ~3%.
- The game is deterministic: no `LD A,R` in code (the one `ED 5F` byte pair is graphics at
  `$5754`), so an A/B run with the same keys per game frame must give identical memory.

## Controls (read from the code, `$FE22` / `$A602` / `$F17B`)

Q accelerate (and turns the key to start), A brake, O left, P right, W / S gear up / down
(stick shift), SPACE centres the steering, 0 aborts the replay. Menus: SPACE, 1 keyboard,
L / R drive on the left / right, SPACE through the track map, then the transmission screen counts
down to AUTO on its own.

## The render, per game frame (original game, Q held, 4 frames traced)

| Routine | What it is | Cost |
| --- | --- | --- |
| `$9EA9` own code | object list scan (`$9F0D`, ~270 objects a frame, ~200 T each), clipping, set-up; also the 8x16 multiply `$C52C` reached by `JP` (~180 a frame, ~300 T each) | 19-23% |
| `$D77D` | perspective divide, HL = N*256/DE (8.8 result); 2 per projected point, ~190-240 a frame, 884 T each | **19-21%** |
| `$C7C0` | polygon fill into the off-screen buffer (self-modifying, `$C5C0-$C6xx`) | 10-15% |
| `$D548` / `$D6E3` | box corners, then project one point (3 x `$D743` + 2 x `$D77D`); ~90 points a frame, 2,660 T each | 25-29% incl. |
| `$D743` | HL += sign-extended A << n (n from the self-modifying stub at `$91BA`) | 4-5% |
| `$DBBE` | fill the buffer: ground dither `$8800-$8FFF`, mountains `$8400-$87FF` (LDIR), sky `$8000-$83FF` | 4-5% |
| `$DC37` / `$DC45` | copy the 4K buffer `$8000-$8FFF` to the screen (POP / PUSH) | 6-8% |
| `$D9B4`, `$DA4C`, `$CEF2` | polygon set-up and edge clipping | 6-9% |

Off-screen buffer: `$8000-$8FFF`, 32 bytes x 128 lines, linear. Projected points: table at `$9C00`
(4 bytes each: x 8.8, y 8.8), written at `$D724`; the low (fraction) bytes ARE read later by the
clipper (`$DA6A` pops whole words), so the divide's fraction cannot be dropped without changing
the picture.

## Patches so far (all output-identical)

| Patch | Change | Saving (full race A/B) |
| --- | --- | --- |
| p01 | `$D77D` divide: when N < DE (97.5% of calls) the whole-number byte is 0 and the remainder is N, so skip its 9 trial subtractions and join the fraction half at `$D7CB`. Slow path is the original, folded into a loop to fit 78 bytes. | ~8% |
| p02 | `$D743`: sign-extend with `RLA / SBC A,A` (8 T) instead of `CP / CCF / LD / SBC` (29 T) | ~0.5% |
| p03 | `$D76D`, `$A0FC`: the code that rewrites the `$91BA` shift stub writes RET instead of NOP after the shifts, so a 0-shift call is CALL + RET | ~0.4% |
| **p01-p03** | | **7.3% over a whole race (629 frames, to GAME OVER, including off-road, a crash and the instant replay); 9.0% on a 150-frame drive** |

How they are proved:

1. `tests/test_p01_divide.py` - the divide alone, original vs patched, every register and flag
   compared (A, F, BC, DE, HL, A', F', SP, exit PC) over edge cases and random inputs. A
   deliberately broken patch fails it.
2. `tools/abtest.py FRAMES p01 p02 p03` - the whole game twice from the same race start, the same
   keys held on each rendered frame (sync at `$DC37`), all 128K compared after every frame
   (except the patched bytes and the `$91BA` stub that p03 changes on purpose). A deliberately
   broken patch is reported on frame 0.
3. `tools/make_tap.py` patches the tape; the patched tape's loaded memory equals the original
   tape's loaded memory with the patches applied, and it reaches a race and drives.

## Next candidates (estimated, not measured)

| Candidate | Estimate | Note |
| --- | --- | --- |
| Object scan `$9F0D`: keep the camera X in BC and skip records with POPs instead of reloading the pointer from memory each time | 2-4% | must leave `$968B` and `$A94E` as the original does at every exit |
| 8x16 multiply `$C52C` via a quarter-square table | ~3% | needs ~1K of memory nothing else uses - not yet found |
| Divide fraction half: non-restoring, two unrolled paths | ~1% | needs ~130 bytes |
| Mountains `LDIR` in `$DC0B` as unrolled `LDI` | ~0.7% | needs 64 bytes |
| Negate `$D773` (64 T) | ~0.4% | check every caller ignores A and flags |

**An honest ceiling:** with output-identical changes only, the total is likely to top out around
25-30% (from ~4 to ~5 frames a second). Getting to "playable" probably needs choices that change
the picture slightly - for example a lower-precision divide, fewer distant objects, or skipping the
horizon redraw when the view has not turned. Those are Grant's decisions, not Claude's.
