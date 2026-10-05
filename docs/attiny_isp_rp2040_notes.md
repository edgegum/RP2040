# RP2040 to ATtiny ISP bench notes

Goal: use the RP2040 as a safe first ISP probe for an Iteaduino Tiny/ATtiny.

Current wiring:

```text
RP2040 3V3  -> ATtiny VCC
RP2040 GND  -> ATtiny GND
RP2040 GP29 -> ATtiny RESET
RP2040 GP28 -> ATtiny SCK
RP2040 GP5  -> ATtiny MISO
RP2040 GP4  -> ATtiny MOSI
```

Rules:

- Power the ATtiny from RP2040 3V3.
- Do not connect the Iteaduino Tiny USB at the same time.
- First test is read-only: read AVR signature via ISP.
- Expected ATtiny85 signature: `1E 93 0B`.
- If signature is `FF FF FF` or `00 00 00`, check pinout, RESET, power, or swapped MOSI/MISO.

Script:

```text
attiny_isp_signature_rp2040.py
```

Read-only inspector:

```text
attiny_isp_inspector_rp2040.py
```

This inspector reads signature, lock byte, fuses, calibration byte, and
small flash/EEPROM previews. It does not erase or write flash, EEPROM, or
fuses.

Full read-only dump:

```text
attiny_isp_dump_hex_rp2040.py
```

This dumper prints ATtiny85 flash and EEPROM as Intel HEX records through
the Thonny console.

PC-side dump analyzer:

```text
python attiny_hex_analyzer.py thonny_dump.txt
```

The analyzer extracts FLASH/EEPROM Intel HEX sections from a copied Thonny
log, writes `.hex` and `.bin` files, then summarizes vectors, strings, and
possible compact data/font rows.

Backup files directly on the RP2040:

```text
attiny_isp_backup_files_rp2040.py
```

This creates `attiny85_flash_backup.hex`, `attiny85_eeprom_backup.hex`, and
`attiny85_info_backup.txt` on the RP2040 filesystem for download through
Thonny.

Flash writer:

```text
attiny_isp_flash_writer_rp2040.py
```

Paste an ATtiny85 Intel HEX program into `TARGET_HEX`, set
`CONFIRM_ERASE_AND_WRITE = "YES"`, then run it from Thonny. This performs
chip erase, page programs flash, and verifies flash. It does not write fuses,
lock bits, or EEPROM.

First write test:

```text
attiny85_blink_d1_program.md
```

The current `attiny_isp_flash_writer_rp2040.py` is loaded with a minimal
D1/PB1 blink Intel HEX program. Leave it at `CONFIRM_ERASE_AND_WRITE = "NO"`
until the backup files have been downloaded from the RP2040.
