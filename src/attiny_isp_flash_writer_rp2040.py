"""
RP2040 -> ATtiny85 ISP flash writer from embedded Intel HEX.

WARNING: this script erases and rewrites the ATtiny85 flash when enabled.
The current fuses show EESAVE is unprogrammed, so a chip erase may also
erase EEPROM. Back up the chip before using this.

Workflow:

  1. Generate or paste an ATtiny85 Intel HEX program into TARGET_HEX below.
  2. Confirm the backup exists.
  3. Change CONFIRM_ERASE_AND_WRITE to "YES".
  4. Run from Thonny on the RP2040.

This script only programs flash. It does not write fuses, lock bits, or
EEPROM.
"""

from machine import Pin
import time


PIN_RESET = 29
PIN_SCK = 28
PIN_MISO = 5
PIN_MOSI = 4

HALF_CYCLE_US = 20
FLASH_BYTES = 8192
PAGE_BYTES = 64

CONFIRM_ERASE_AND_WRITE = "NO"

# First write test: blink D1/PB1 forever.
#
# If your board LED is active-low, the LED will still blink; only the
# logical on/off phase is inverted.
TARGET_HEX = """
:1000000000C0B99AC19A03D0C19801D0FBCF20E5B6
:100010003FEF4FEF4A95F1F73A95D9F72A95C1F797
:02002000089541
:00000001FF
"""

reset = Pin(PIN_RESET, Pin.OUT, value=1)
sck = Pin(PIN_SCK, Pin.OUT, value=0)
mosi = Pin(PIN_MOSI, Pin.OUT, value=0)
miso = Pin(PIN_MISO, Pin.IN)


def spi_xfer(byte):
    value = 0
    for bit in range(7, -1, -1):
        mosi.value((byte >> bit) & 1)
        time.sleep_us(HALF_CYCLE_US)
        sck.value(1)
        time.sleep_us(HALF_CYCLE_US)
        value = (value << 1) | miso.value()
        sck.value(0)
        time.sleep_us(HALF_CYCLE_US)
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


def chip_erase():
    print("chip erase...")
    isp_command(0xAC, 0x80, 0x00, 0x00)
    time.sleep_ms(20)


def load_flash_page_byte(byte_address, value):
    word_address = byte_address >> 1
    command = 0x48 if byte_address & 1 else 0x40
    isp_command(command, (word_address >> 8) & 0xFF, word_address & 0xFF, value)


def write_flash_page(page_start):
    word_address = page_start >> 1
    isp_command(0x4C, (word_address >> 8) & 0xFF, word_address & 0xFF, 0x00)
    time.sleep_ms(10)


def parse_hex_byte(text):
    return int(text, 16)


def parse_intel_hex(hex_text):
    image = bytearray([0xFF] * FLASH_BYTES)
    highest = -1
    base = 0

    for raw_line in hex_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue
        if not line.startswith(":"):
            raise ValueError("not an Intel HEX line: " + line)

        count = parse_hex_byte(line[1:3])
        address = parse_hex_byte(line[3:7])
        record_type = parse_hex_byte(line[7:9])
        data = [parse_hex_byte(line[9 + i * 2:11 + i * 2]) for i in range(count)]
        checksum = parse_hex_byte(line[9 + count * 2:11 + count * 2])
        total = count + (address >> 8) + (address & 0xFF) + record_type + sum(data) + checksum
        if (total & 0xFF) != 0:
            raise ValueError("bad checksum: " + line)

        if record_type == 0x00:
            absolute = base + address
            if absolute + count > FLASH_BYTES:
                raise ValueError("HEX data exceeds ATtiny85 flash")
            for offset, value in enumerate(data):
                image[absolute + offset] = value
            if count:
                highest = max(highest, absolute + count - 1)
        elif record_type == 0x01:
            break
        elif record_type == 0x04:
            if count != 2:
                raise ValueError("bad extended linear address record")
            base = ((data[0] << 8) | data[1]) << 16
            if base != 0:
                raise ValueError("ATtiny85 HEX must stay below 64 KiB")
        else:
            raise ValueError("unsupported HEX record type: " + str(record_type))

    return image, highest


def program_flash(image, highest):
    if highest < 0:
        print("HEX contains no flash data.")
        return

    limit = ((highest // PAGE_BYTES) + 1) * PAGE_BYTES
    print("programming", limit, "bytes")
    for page_start in range(0, limit, PAGE_BYTES):
        page = image[page_start:page_start + PAGE_BYTES]
        if all(value == 0xFF for value in page):
            continue
        for offset, value in enumerate(page):
            if value != 0xFF:
                load_flash_page_byte(page_start + offset, value)
        write_flash_page(page_start)
        print(" page 0x{:04X}".format(page_start))


def verify_flash(image, highest):
    print("verifying...")
    errors = 0
    for address in range(highest + 1):
        expected = image[address]
        actual = read_flash_byte(address)
        if actual != expected:
            print(" mismatch 0x{:04X}: expected {:02X}, read {:02X}".format(
                address, expected, actual
            ))
            errors += 1
            if errors >= 16:
                break
    if errors:
        print("VERIFY FAILED:", errors, "shown")
        return False
    print("verify OK")
    return True


def fmt_bytes(values):
    return " ".join("{:02X}".format(value) for value in values)


def main():
    print("RP2040 ATtiny85 ISP flash writer")
    print("This script can erase/write flash when explicitly enabled.")

    if CONFIRM_ERASE_AND_WRITE != "YES":
        print("Refusing to write. Set CONFIRM_ERASE_AND_WRITE = \"YES\" first.")
        return

    image, highest = parse_intel_hex(TARGET_HEX)
    if highest < 0:
        print("Refusing to write empty HEX.")
        return

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
        print("Not an ATtiny85 signature; stopping.")
        return

    chip_erase()
    program_flash(image, highest)
    ok = verify_flash(image, highest)

    leave_programming()
    if ok:
        print("Done. Chip programmed and left out of programming mode.")
    else:
        print("Done with verification errors. Keep the backup.")


main()
