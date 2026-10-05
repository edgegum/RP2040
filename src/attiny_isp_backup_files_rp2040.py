"""
RP2040 -> ATtiny85 ISP backup-to-files tool.

This read-only script saves the current ATtiny85 contents to files on the
RP2040 filesystem. In Thonny, use the device file browser to download them
to the PC after the script finishes.

Files created on the RP2040:

  attiny85_flash_backup.hex
  attiny85_eeprom_backup.hex
  attiny85_info_backup.txt

No erase or write commands are implemented here.
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

FLASH_FILE = "attiny85_flash_backup.hex"
EEPROM_FILE = "attiny85_eeprom_backup.hex"
INFO_FILE = "attiny85_info_backup.txt"

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


def read_lock_byte():
    return isp_command(0x58, 0x00, 0x00, 0x00)[3]


def read_fuses():
    return {
        "low": isp_command(0x50, 0x00, 0x00, 0x00)[3],
        "high": isp_command(0x58, 0x08, 0x00, 0x00)[3],
        "extended": isp_command(0x50, 0x08, 0x00, 0x00)[3],
    }


def read_calibration_byte():
    return isp_command(0x38, 0x00, 0x00, 0x00)[3]


def read_flash_byte(byte_address):
    word_address = byte_address >> 1
    command = 0x28 if byte_address & 1 else 0x20
    return isp_command(command, (word_address >> 8) & 0xFF, word_address & 0xFF, 0x00)[3]


def read_eeprom_byte(address):
    return isp_command(0xA0, (address >> 8) & 0xFF, address & 0xFF, 0x00)[3]


def intel_hex_record(address, record_type, data):
    count = len(data)
    total = count + ((address >> 8) & 0xFF) + (address & 0xFF) + record_type
    total += sum(data)
    checksum = ((~total + 1) & 0xFF)
    body = [count, (address >> 8) & 0xFF, address & 0xFF, record_type] + data + [checksum]
    return ":" + "".join("{:02X}".format(value) for value in body)


def write_hex_file(filename, read_func, total_bytes):
    print("writing", filename)
    with open(filename, "w") as output:
        address = 0
        while address < total_bytes:
            row_len = min(ROW_BYTES, total_bytes - address)
            data = [read_func(address + offset) for offset in range(row_len)]
            output.write(intel_hex_record(address, 0x00, data) + "\n")
            address += row_len
            if address % 512 == 0:
                print(" ", filename, address, "bytes")
        output.write(intel_hex_record(0x0000, 0x01, []) + "\n")


def fmt_bytes(values):
    return " ".join("{:02X}".format(value) for value in values)


def main():
    print("RP2040 ATtiny85 ISP backup-to-files")
    print("Read-only: no erase or write commands are implemented.")

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

    fuses = read_fuses()
    lock = read_lock_byte()
    calibration = read_calibration_byte()

    with open(INFO_FILE, "w") as info:
        info.write("signature: {}\n".format(fmt_bytes(signature)))
        info.write("lock byte: 0x{:02X}\n".format(lock))
        info.write("fuse low: 0x{:02X}\n".format(fuses["low"]))
        info.write("fuse high: 0x{:02X}\n".format(fuses["high"]))
        info.write("fuse extended: 0x{:02X}\n".format(fuses["extended"]))
        info.write("calibration byte: 0x{:02X}\n".format(calibration))

    write_hex_file(FLASH_FILE, read_flash_byte, FLASH_BYTES)
    write_hex_file(EEPROM_FILE, read_eeprom_byte, EEPROM_BYTES)

    leave_programming()
    print("Done. Download these files from the RP2040:")
    print(" ", FLASH_FILE)
    print(" ", EEPROM_FILE)
    print(" ", INFO_FILE)


main()
