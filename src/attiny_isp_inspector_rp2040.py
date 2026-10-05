"""
RP2040 -> ATtiny ISP read-only inspector.

This script enters AVR ISP mode and reads information the chip can expose
without erasing or writing anything:

  - device signature
  - lock byte
  - low/high/extended fuses
  - oscillator calibration byte
  - first bytes of flash
  - first bytes of EEPROM

It intentionally does not implement chip erase, flash write, EEPROM write,
or fuse write commands.

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

# Slow ISP is friendly to ATtiny parts running from their default clock.
HALF_CYCLE_US = 20

# Keep initial dumps short enough for Thonny output to stay readable.
FLASH_DUMP_BYTES = 128
EEPROM_DUMP_BYTES = 64

reset = Pin(PIN_RESET, Pin.OUT, value=1)
sck = Pin(PIN_SCK, Pin.OUT, value=0)
mosi = Pin(PIN_MOSI, Pin.OUT, value=0)
miso = Pin(PIN_MISO, Pin.IN)


DEVICES = {
    (0x1E, 0x90, 0x07): {
        "name": "ATtiny13",
        "flash": 1024,
        "eeprom": 64,
        "fuse_model": "tiny13",
    },
    (0x1E, 0x91, 0x08): {
        "name": "ATtiny25",
        "flash": 2048,
        "eeprom": 128,
        "fuse_model": "tinyx5",
    },
    (0x1E, 0x92, 0x06): {
        "name": "ATtiny45",
        "flash": 4096,
        "eeprom": 256,
        "fuse_model": "tinyx5",
    },
    (0x1E, 0x93, 0x0B): {
        "name": "ATtiny85",
        "flash": 8192,
        "eeprom": 512,
        "fuse_model": "tinyx5",
    },
    (0x1E, 0x92, 0x07): {
        "name": "ATtiny44",
        "flash": 4096,
        "eeprom": 256,
        "fuse_model": "generic",
    },
    (0x1E, 0x93, 0x0C): {
        "name": "ATtiny84",
        "flash": 8192,
        "eeprom": 512,
        "fuse_model": "generic",
    },
}


def delay_us(us):
    time.sleep_us(us)


def spi_xfer(byte):
    """SPI mode 0, MSB first, bit-banged slowly."""
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
    sig = []
    for index in range(3):
        sig.append(isp_command(0x30, 0x00, index, 0x00)[3])
    return sig


def read_lock_byte():
    return isp_command(0x58, 0x00, 0x00, 0x00)[3]


def read_fuses():
    return {
        "low": isp_command(0x50, 0x00, 0x00, 0x00)[3],
        "high": isp_command(0x58, 0x08, 0x00, 0x00)[3],
        "extended": isp_command(0x50, 0x08, 0x00, 0x00)[3],
    }


def read_calibration_byte(index=0):
    return isp_command(0x38, 0x00, index & 0x03, 0x00)[3]


def read_flash_byte(byte_address):
    word_address = byte_address >> 1
    high_addr = (word_address >> 8) & 0xFF
    low_addr = word_address & 0xFF
    command = 0x28 if byte_address & 1 else 0x20
    return isp_command(command, high_addr, low_addr, 0x00)[3]


def read_eeprom_byte(address):
    return isp_command(0xA0, (address >> 8) & 0xFF, address & 0xFF, 0x00)[3]


def fmt_byte(value):
    return "{:02X}".format(value)


def fmt_bytes(values):
    return " ".join(fmt_byte(v) for v in values)


def printable(value):
    if 32 <= value <= 126:
        return chr(value)
    return "."


def dump_bytes(title, read_func, total):
    print()
    print("{} ({} bytes):".format(title, total))
    address = 0
    while address < total:
        row = [read_func(address + offset) for offset in range(min(16, total - address))]
        text = "".join(printable(v) for v in row)
        print("  {:04X}: {:47}  {}".format(address, fmt_bytes(row), text))
        address += len(row)


def bit_state(value, bit):
    return "programmed/0" if (value & (1 << bit)) == 0 else "unprogrammed/1"


def decode_tinyx5_fuses(fuses):
    low = fuses["low"]
    high = fuses["high"]
    extended = fuses["extended"]

    print()
    print("ATtiny25/45/85 fuse hints:")
    print("  CKDIV8:", bit_state(low, 7))
    print("  CKOUT: ", bit_state(low, 6))
    print("  SUT:   {}".format((low >> 4) & 0x03))
    print("  CKSEL: {}".format(low & 0x0F))
    print("  RSTDISBL:", bit_state(high, 7))
    print("  DWEN:    ", bit_state(high, 6))
    print("  SPIEN:   ", bit_state(high, 5))
    print("  WDTON:   ", bit_state(high, 4))
    print("  EESAVE:  ", bit_state(high, 3))
    print("  BODLEVEL:", extended & 0x07)
    if (high & (1 << 7)) == 0:
        print("  warning: RESET pin is disabled; normal ISP would usually fail.")
    if (high & (1 << 5)) != 0:
        print("  warning: SPIEN appears unprogrammed; normal ISP would usually fail.")


def decode_generic_fuses(fuses):
    print()
    print("Generic fuse hints:")
    print("  low:      0x{}".format(fmt_byte(fuses["low"])))
    print("  high:     0x{}".format(fmt_byte(fuses["high"])))
    print("  extended: 0x{}".format(fmt_byte(fuses["extended"])))
    print("  Note: detailed bit meanings vary by ATtiny family.")


def main():
    print("RP2040 ATtiny ISP read-only inspector")
    print("Pins: RESET=GP{} SCK=GP{} MISO=GP{} MOSI=GP{}".format(
        PIN_RESET, PIN_SCK, PIN_MISO, PIN_MOSI
    ))
    print("Read-only commands only. No erase, write, or fuse programming.")
    print()

    enable_response = enter_programming()
    print("enable:", fmt_bytes(enable_response))
    if enable_response[2] != 0x53:
        print("warning: programming enable did not echo 53")

    sig = read_signature()
    device = DEVICES.get(tuple(sig))
    name = device["name"] if device else "unknown"
    print("signature:", fmt_bytes(sig), name)

    if sig[0] != 0x1E:
        leave_programming()
        print("No AVR signature detected; stopping before further reads.")
        return

    lock = read_lock_byte()
    fuses = read_fuses()
    calibration = read_calibration_byte()

    print("lock byte: 0x{}".format(fmt_byte(lock)))
    print("fuse low: 0x{}".format(fmt_byte(fuses["low"])))
    print("fuse high: 0x{}".format(fmt_byte(fuses["high"])))
    print("fuse extended: 0x{}".format(fmt_byte(fuses["extended"])))
    print("calibration byte: 0x{}".format(fmt_byte(calibration)))

    if device and device["fuse_model"] == "tinyx5":
        decode_tinyx5_fuses(fuses)
    else:
        decode_generic_fuses(fuses)

    flash_total = FLASH_DUMP_BYTES
    eeprom_total = EEPROM_DUMP_BYTES
    if device:
        flash_total = min(FLASH_DUMP_BYTES, device["flash"])
        eeprom_total = min(EEPROM_DUMP_BYTES, device["eeprom"])

    dump_bytes("flash preview", read_flash_byte, flash_total)
    dump_bytes("EEPROM preview", read_eeprom_byte, eeprom_total)

    leave_programming()
    print()
    print("Done. Chip left out of programming mode.")


main()
