"""
Analyze ATtiny Intel HEX copied from the RP2040/Thonny dumper.

Usage:

  python attiny_hex_analyzer.py thonny_dump.txt

The input may be the raw Thonny console output. The script extracts FLASH
and EEPROM Intel HEX sections, writes .hex/.bin files next to the input, and
prints a compact summary with reset/vector jumps, used range, ASCII strings,
and possible 8-byte font/data rows.
"""

from __future__ import annotations

import argparse
from pathlib import Path


SECTION_BEGIN = "; BEGIN "
SECTION_END = "; END "


def parse_ihex_line(line: str):
    line = line.strip()
    if not line.startswith(":"):
        return None
    raw = bytes.fromhex(line[1:])
    count = raw[0]
    address = (raw[1] << 8) | raw[2]
    record_type = raw[3]
    data = raw[4:4 + count]
    checksum = raw[4 + count]
    if ((sum(raw[:-1]) + checksum) & 0xFF) != 0:
        raise ValueError("bad checksum in {}".format(line))
    return address, record_type, data


def extract_sections(text: str):
    sections = {}
    current = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(SECTION_BEGIN):
            label = line[len(SECTION_BEGIN):].replace(" Intel HEX", "").strip()
            current = label
            sections[current] = []
        elif line.startswith(SECTION_END):
            current = None
        elif current and line.startswith(":"):
            sections[current].append(line)
    return sections


def ihex_to_binary(lines):
    image = bytearray()
    for line in lines:
        parsed = parse_ihex_line(line)
        if not parsed:
            continue
        address, record_type, data = parsed
        if record_type == 0x01:
            break
        if record_type != 0x00:
            continue
        end = address + len(data)
        if end > len(image):
            image.extend(b"\xFF" * (end - len(image)))
        image[address:end] = data
    return bytes(image)


def write_ihex(path: Path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def find_used_range(data: bytes):
    used = [index for index, value in enumerate(data) if value != 0xFF]
    if not used:
        return None
    return min(used), max(used)


def find_ascii_strings(data: bytes, min_len=4):
    strings = []
    start = None
    buf = []
    for index, value in enumerate(data + b"\x00"):
        if 32 <= value <= 126:
            if start is None:
                start = index
            buf.append(chr(value))
        else:
            if start is not None and len(buf) >= min_len:
                strings.append((start, "".join(buf)))
            start = None
            buf = []
    return strings


def decode_rjmp(word):
    offset = word & 0x0FFF
    if offset & 0x0800:
        offset -= 0x1000
    return offset


def summarize_vectors(flash: bytes, count=16):
    print("Vectors / reset table:")
    for vector in range(count):
        address = vector * 2
        if address + 1 >= len(flash):
            break
        word = flash[address] | (flash[address + 1] << 8)
        if (word & 0xF000) == 0xC000:
            target_word = vector + 1 + decode_rjmp(word)
            print("  {:02d} @ 0x{:04X}: RJMP 0x{:04X}".format(
                vector, address, target_word * 2
            ))
        else:
            print("  {:02d} @ 0x{:04X}: word 0x{:04X}".format(vector, address, word))


def show_possible_font_rows(data: bytes):
    print("Possible 8-byte glyph/data rows:")
    shown = 0
    for address in range(0, len(data) - 8 + 1, 8):
        row = data[address:address + 8]
        if row in (b"\xFF" * 8, b"\x00" * 8):
            continue
        printableish = sum(1 for value in row if value in (0, 0x18, 0x3C, 0x7E, 0x66, 0x63, 0x7F))
        if printableish >= 4:
            print("  0x{:04X}: {}".format(address, " ".join("{:02X}".format(v) for v in row)))
            shown += 1
            if shown >= 16:
                break
    if shown == 0:
        print("  none obvious")


def analyze_image(label: str, data: bytes):
    print()
    print(label)
    print("-" * len(label))
    print("size: {} bytes".format(len(data)))
    used = find_used_range(data)
    if used:
        print("non-FF range: 0x{:04X}..0x{:04X} ({} bytes)".format(
            used[0], used[1], used[1] - used[0] + 1
        ))
    else:
        print("non-FF range: none")

    strings = find_ascii_strings(data)
    if strings:
        print("ASCII strings:")
        for address, text in strings[:20]:
            print("  0x{:04X}: {!r}".format(address, text))
    else:
        print("ASCII strings: none")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dump", type=Path)
    args = parser.parse_args()

    text = args.dump.read_text(encoding="utf-8", errors="replace")
    sections = extract_sections(text)
    if not sections:
        raise SystemExit("No '; BEGIN ... Intel HEX' sections found.")

    for label, lines in sections.items():
        stem = args.dump.with_suffix("")
        hex_path = stem.with_name(stem.name + "_" + label.lower() + ".hex")
        bin_path = stem.with_name(stem.name + "_" + label.lower() + ".bin")
        write_ihex(hex_path, lines)
        data = ihex_to_binary(lines)
        bin_path.write_bytes(data)
        print("wrote {}".format(hex_path))
        print("wrote {}".format(bin_path))
        analyze_image(label, data)
        if label.upper() == "FLASH":
            summarize_vectors(data)
            show_possible_font_rows(data)


if __name__ == "__main__":
    main()
