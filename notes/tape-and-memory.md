# Tape and memory (measured 9 Nov 2026)

`HARD128.TAP` (47,211 bytes), all checksums pass:

| Block | What | Load |
| --- | --- | --- |
| 0-1 | BASIC "HD 128K", LINE 10 | |
| 2-3 | CODE | 30000, 100 |
| 4-5 | CODE | 32960, 5000 |
| 6-7 | CODE | 43616, 200 |
| 8-9 | BASIC "-" | 23755, 84 |
| 10-11 | CODE | 24000, 41400 |

- `tap2sna.py -c machine=128` (fast load) ends with PC=23316 (RAM).
- After the title screen: port 7FFD = 0x13, so RAM bank 3 is at C000 and the 48K BASIC ROM (ROM 1) is paged in.
- The game reaches its controls menu (1 Keyboard, 2 Kempston, 3 Fuller, 4 Interface 2, 5 Cursor; SPACE centres steering; 0 aborts replay/offroad).
- In the plain 48K emulator (`zx` package) the tape resets to the copyright screen: it needs a 128K.
