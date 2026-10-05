"""
RP2040 -> ATtiny ISP signature reader.

Safe first test: this script only enters AVR ISP mode and reads the
3-byte device signature. It does not erase or write flash/fuses.

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

reset = Pin(PIN_RESET, Pin.OUT, value=1)
sck = Pin(PIN_SCK, Pin.OUT, value=0)
mosi = Pin(PIN_MOSI, Pin.OUT, value=0)
miso = Pin(PIN_MISO, Pin.IN)


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

    # Programming Enable: response byte 3 should usually echo 0x53.
    return isp_command(0xAC, 0x53, 0x00, 0x00)


def leave_programming():
    sck.value(0)
    mosi.value(0)
    reset.value(1)
    time.sleep_ms(20)


def read_signature():
    sig = []
    for index in range(3):
        response = isp_command(0x30, 0x00, index, 0x00)
        sig.append(response[3])
    return sig


def classify_signature(sig):
    known = {
        (0x1E, 0x90, 0x07): "ATtiny13",
        (0x1E, 0x91, 0x08): "ATtiny25",
        (0x1E, 0x92, 0x06): "ATtiny45",
        (0x1E, 0x93, 0x0B): "ATtiny85",
        (0x1E, 0x92, 0x07): "ATtiny44",
        (0x1E, 0x93, 0x0C): "ATtiny84",
    }
    return known.get(tuple(sig), "unknown")


def fmt_bytes(values):
    return " ".join("{:02X}".format(v) for v in values)


def main():
    print("RP2040 ATtiny ISP signature reader")
    print("Pins: RESET=GP{} SCK=GP{} MISO=GP{} MOSI=GP{}".format(
        PIN_RESET, PIN_SCK, PIN_MISO, PIN_MOSI
    ))
    print("Power: ATtiny from RP2040 3V3 only; Iteaduino USB disconnected.")
    print()

    for attempt in range(1, 6):
        print("Attempt", attempt)
        enable_response = enter_programming()
        print("  enable:", fmt_bytes(enable_response))

        sig = read_signature()
        name = classify_signature(sig)
        print("  signature:", fmt_bytes(sig), name)

        leave_programming()

        if sig[0] == 0x1E and sig != [0xFF, 0xFF, 0xFF] and sig != [0x00, 0x00, 0x00]:
            print("OK: AVR signature detected.")
            return

        time.sleep_ms(250)

    print()
    print("No valid signature yet.")
    print("Check VCC=3.3V, GND, RESET, MOSI/MISO swapped, and SCK wiring.")


main()
