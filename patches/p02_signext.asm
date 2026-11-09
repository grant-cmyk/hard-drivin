; Patch 02 - faster sign extension in $D743 (bank 0, $D743-$D755)
;
; $D743: HL = HL + (sign-extended A << n), n set by self-modifying code at
; $91BA. The original sign-extends A with CP $80 / CCF / LD A,0 / SBC A,0
; (29 T-states); RLA / SBC A,A gives the same A ($00 or $FF) in 8.
; Everything the caller sees is unchanged: A, HL and every flag come from the
; same AND A / ADC HL,DE at the end; DE is saved and restored as before.
; Called ~290 times a game frame.
        org $D743
        push de
        ex de,hl
        ld l,a
        rla                 ; carry = bit 7 of A
        sbc a,a             ; A = $00 or $FF
        ld h,a
        call $91BA          ; HL <<= n (self-modified)
        and a
        adc hl,de
        pop de
        ret
        ds $D756-$,0        ; 5 spare bytes, never executed
