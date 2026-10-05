"""
RP2040 -> ATtiny85 ISP full read-only dumper.

This script reads the ATtiny flash and EEPROM and prints them as Intel HEX.
It does not erase or write flash, EEPROM, lock bits, or fuses.

The output can be copied from Thonny and saved as .hex/.eep files on the PC.

Wiring for the current bench setup:

  RP2040 3V3  -> ATtiny VCC
  RP2040 GND  -> ATtiny GND
  RP2040 GP29 -> ATtiny RESET
  RP2040 GP28 -> ATtiny SCK
  RP2040 GP5  -> ATtiny MISO
  RP2040 GP4  -> ATtiny MOSI

Do not connect the Iteaduino Tiny USB while powering it from RP2040 3V3.
"""

from machine import Pin
import time


PIN_RESET = 29
PIN_SCK = 28
PIN_MISO = 5
PIN_MOSI = 4

HALF_CYCLE_US = 20

FLASH_BYTES = 8192
EEPROM_BYTES = 512
ROW_BYTES = 16

reset = Pin(PIN_RESET, Pin.OUT, value=1)
sck = Pin(PIN_SCK, Pin.OUT, value=0)
mosi = Pin(PIN_MOSI, Pin.OUT, value=0)
miso = Pin(PIN_MISO, Pin.IN)


def delay_us(us):
    time.sleep_us(us)


def spi_xfer(byte):
    value = 0
    for bit in range(7, -1, -1):
        mosi.value((byte >> bit) & 1)
        delay_us(HALF_CYCLE_US)
        sck.value(1)
        delay_us(HALF_CYCLE_US)
        value = (value << 1) | miso.value()
        sck.value(0)
        delay_us(HALF_CYCLE_US)
    return value


def isp_command(a, b, c, d):
    return (
        spi_xfer(a),
        spi_xfer(b),
        spi_xfer(c),
        spi_xfer(d),
    )


def enter_programming():
    reset.value(1)
    sck.value(0)
    mosi.value(0)
    time.sleep_ms(50)
    reset.value(0)
    time.sleep_ms(30)
    return isp_command(0xAC, 0x53, 0x00, 0x00)


def leave_programming():
    sck.value(0)
    mosi.value(0)
    reset.value(1)
    time.sleep_ms(20)


def read_signature():
    return [isp_command(0x30, 0x00, index, 0x00)[3] for index in range(3)]


def read_flash_byte(byte_address):
    word_address = byte_address >> 1
    command = 0x28 if byte_address & 1 else 0x20
    return isp_command(command, (word_address >> 8) & 0xFF, word_address & 0xFF, 0x00)[3]


def read_eeprom_byte(address):
    return isp_command(0xA0, (address >> 8) & 0xFF, address & 0xFF, 0x00)[3]


def fmt_bytes(values):
    return " ".join("{:02X}".format(v) for v in values)


def intel_hex_record(address, record_type, data):
    count = len(data)
    total = count + ((address >> 8) & 0xFF) + (address & 0xFF) + record_type
    total += sum(data)
    checksum = ((~total + 1) & 0xFF)
    body = [count, (address >> 8) & 0xFF, address & 0xFF, record_type] + data + [checksum]
    return ":" + "".join("{:02X}".format(v) for v in body)


def dump_intel_hex(title, read_func, total_bytes):
    print()
    print("; BEGIN {} Intel HEX".format(title))
    address = 0
    while address < total_bytes:
        row_len = min(ROW_BYTES, total_bytes - address)
        data = [read_func(address + offset) for offset in range(row_len)]
        print(intel_hex_record(address, 0x00, data))
        address += row_len
        if address % 512 == 0:
            print("; {} bytes read".format(address))
    print(intel_hex_record(0x0000, 0x01, []))
    print("; END {} Intel HEX".format(title))


def main():
    print("RP2040 ATtiny85 ISP full read-only dumper")
    print("Pins: RESET=GP{} SCK=GP{} MISO=GP{} MOSI=GP{}".format(
        PIN_RESET, PIN_SCK, PIN_MISO, PIN_MOSI
    ))
    print("No erase or write commands are implemented.")
    print()

    enable = enter_programming()
    print("enable:", fmt_bytes(enable))
    if enable[2] != 0x53:
        leave_programming()
        print("Programming enable failed; stopping.")
        return

    signature = read_signature()
    print("signature:", fmt_bytes(signature))
    if signature != [0x1E, 0x93, 0x0B]:
        leave_programming()
        print("Not an ATtiny85 signature; stopping to avoid wrong size assumptions.")
        return

    dump_intel_hex("FLASH", read_flash_byte, FLASH_BYTES)
    dump_intel_hex("EEPROM", read_eeprom_byte, EEPROM_BYTES)

    leave_programming()
    print()
    print("Done. Chip left out of programming mode.")


main()
