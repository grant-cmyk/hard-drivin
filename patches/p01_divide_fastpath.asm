; Patch 01 - perspective divide fast path (bank 0, $D77D-$D7CA)
;
; $D77D computes HL = (N * 256) / DE, N = HL on entry, as an 8.8 result.
; The original always runs 9 trial subtractions for the whole-number byte
; before the 8 for the fraction. Measured in a race: N < DE in ~97.5% of
; calls, which makes the whole-number byte 0 and leaves the remainder = N,
; so all 9 of those subtractions are wasted.
;
; Fast path: if N < DE, set A = $FF (the inverted all-zero quotient byte the
; original builds) and HL = N, and join the original at $D7CB, the fraction
; half, which is untouched. Registers and flags on exit are identical to the
; original (A, F, A', F', HL; BC and DE preserved): the fraction half recomputes
; every flag the caller can see, and the caller discards the main AF.
;
; Slow path (N >= DE): the original instructions, in the same order, with the
; seven identical shift-subtract steps folded into a DJNZ loop so the whole
; routine fits in the original's 78 bytes. BC is saved round the loop (the
; caller keeps a result in BC). Both overflow exits to $D73C stay before the
; PUSH, so the stack they unwind is unchanged.

        org $D77D
div:    and a
        sbc hl,de
        jr nc,slow
        add hl,de           ; HL = N again
        ld a,$FF            ; quotient byte 0, stored inverted
        jr frac
slow:   add hl,de           ; HL = N again
        ld a,l              ; --- original code from here ---
        ld l,h
        ld h,0
        and a
        sbc hl,de
        jp nc,$D73C         ; whole part too big: clip
        add hl,de
        rla
        adc hl,hl
        and a
        sbc hl,de
        jp nc,$D73C         ; clip
        add hl,de
        push bc
        ld b,7
step:   rla
        adc hl,hl
        sbc hl,de
        jr nc,keep
        add hl,de
keep:   djnz step
        pop bc
        rla
        jr frac
pad:    ds $D7CB-pad,0      ; unused bytes, never executed
frac    equ $D7CB
