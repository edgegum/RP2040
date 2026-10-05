"""
RP2040 -> ATtiny UART reader.

Non-invasive test: this script only listens for serial data from the
currently running ATtiny firmware. It does not reset, program, erase, or
write anything to the ATtiny.

Default wiring for the current bench setup:

  RP2040 3V3  -> ATtiny VCC
  RP2040 GND  -> ATtiny GND
  RP2040 GP5  -> ATtiny TX / serial output pin

Optional, only if you want to send data later:

  RP2040 GP4  -> ATtiny RX / serial input pin

Do not connect the Iteaduino Tiny USB while powering it from RP2040 3V3.
If the ATtiny board is powered by its own USB instead, connect GND only
between RP2040 and ATtiny and do not connect RP2040 3V3 to ATtiny VCC.
"""

from machine import Pin, UART
import time


UART_ID = 1
PIN_RX = 5
PIN_TX = 4

# Try one baud at a time. Put the most likely baud first if you know it.
BAUD_RATES = (9600, 19200, 38400, 57600, 115200, 4800, 2400, 1200)
SECONDS_PER_BAUD = 8


def printable(byte):
    if byte in (10, 13):
        return chr(byte)
    if 32 <= byte <= 126:
        return chr(byte)
    return "."


def show_bytes(data):
    text = "".join(printable(b) for b in data)
    hex_values = " ".join("{:02X}".format(b) for b in data)
    print("  text:", repr(text))
    print("  hex: ", hex_values)


def listen_at_baud(baudrate):
    uart = UART(
        UART_ID,
        baudrate=baudrate,
        bits=8,
        parity=None,
        stop=1,
        rx=Pin(PIN_RX),
        tx=Pin(PIN_TX),
        timeout=20,
    )

    print()
    print("Listening at {} baud on UART{} RX=GP{} TX=GP{}".format(
        baudrate, UART_ID, PIN_RX, PIN_TX
    ))
    print("Waiting {} seconds...".format(SECONDS_PER_BAUD))

    start = time.ticks_ms()
    seen = 0

    while time.ticks_diff(time.ticks_ms(), start) < SECONDS_PER_BAUD * 1000:
        waiting = uart.any()
        if waiting:
            data = uart.read(waiting)
            if data:
                seen += len(data)
                show_bytes(data)
        time.sleep_ms(50)

    if seen == 0:
        print("  no bytes seen")
    else:
        print("  total bytes:", seen)

    uart.deinit()


def main():
    print("RP2040 ATtiny UART reader")
    print("Connect ATtiny TX to RP2040 GP{} and share GND.".format(PIN_RX))
    print("This script only listens; it does not touch RESET or ISP.")

    while True:
        for baudrate in BAUD_RATES:
            listen_at_baud(baudrate)


main()
