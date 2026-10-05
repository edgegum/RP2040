# ATtiny85 D1 blink test

Target board assumption:

```text
D1 = PB1
```

This tiny AVR program configures `PB1` as output and toggles it forever.
It is intended as the first flash-write test for the RP2040 ISP workflow.

Intel HEX:

```text
:1000000000C0B99AC19A03D0C19801D0FBCF20E5B6
:100010003FEF4FEF4A95F1F73A95D9F72A95C1F797
:02002000089541
:00000001FF
```

Instruction outline:

```text
0x0000: RJMP reset
reset:
  SBI DDRB, 1       ; D1/PB1 output
loop:
  SBI PORTB, 1      ; LED on, or off if board LED is active-low
  RCALL delay
  CBI PORTB, 1      ; LED off, or on if board LED is active-low
  RCALL delay
  RJMP loop
delay:
  nested DEC/BRNE loops
  RET
```

The delay is intentionally crude but visible. The exact blink rate depends
on the chip clock/fuses.
