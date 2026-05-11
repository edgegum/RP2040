"""
Teste da Matriz LED 8x8 com MAX7219 via Bit-Bang
================================================

Este script testa uma matriz LED 8x8 usando o driver MAX7219
através de comunicação SPI implementada manualmente (bit-bang).

Hardware necessário:
- Matriz LED 8x8
- Driver MAX7219
- Raspberry Pi Pico RP2040

Conexões (usando GPIOs disponíveis):
- DIN: Pino 4  (Data In)
- CS:  Pino 5  (Chip Select)
- CLK: Pino 3  (Clock)
- VCC: 3.3V
- GND: GND

Autor: Original
"""

from machine import Pin
import time

# Usando apenas os GPIOs disponíveis: 29, 28, 5, 4, 3, 2
DIN = Pin(4,  Pin.OUT)  # Data In
CS  = Pin(5,  Pin.OUT)  # Chip Select
CLK = Pin(3,  Pin.OUT)  # Clock

def send_byte(data):
    for i in range(8):
        CLK.off()
        DIN.value((data >> (7 - i)) & 1)
        CLK.on()

def max7219_write(register, data):
    CS.off()
    send_byte(register)
    send_byte(data)
    CS.on()

def max7219_init():
    CS.on()
    max7219_write(0x09, 0x00)  # Decoding: off
    max7219_write(0x0A, 0x0F)  # Brightness: max
    max7219_write(0x0B, 0x07)  # Scan limit: 7 (all digits)
    max7219_write(0x0C, 0x01)  # Shutdown: 1 (normal operation)
    max7219_write(0x0F, 0x00)  # Display test: off
    # Limpa o display
    for i in range(1, 9):
        max7219_write(i, 0)

def clear():
    for i in range(1, 9):
        max7219_write(i, 0)

def show_pattern(pattern, delay=0.2):
    for i, val in enumerate(pattern):
        max7219_write(i+1, val)
    time.sleep(delay)

max7219_init()

# 1. X animado
for _ in range(2):
    for i in range(8):
        row = (1 << i) | (1 << (7 - i))
        pattern = [0]*8
        pattern[i] = row
        show_pattern(pattern, 0.1)
    clear()

# 2. Quadrado girando
square = [
    0b11111111,
    0b10000001,
    0b10000001,
    0b10000001,
    0b10000001,
    0b10000001,
    0b10000001,
    0b11111111
]
for _ in range(2):
    show_pattern(square, 0.4)
    show_pattern([0b00000000]*8, 0.2)
clear()

# 3. Snake (cobrinha)
snake = [0b00000001]
for i in range(1, 8):
    snake.append(snake[-1] << 1)
for s in snake + snake[::-1]:
    show_pattern([s]*8, 0.1)
clear()

# 4. Círculo piscando
circle = [
    0b00111100,
    0b01111110,
    0b11111111,
    0b11111111,
    0b11111111,
    0b11111111,
    0b01111110,
    0b00111100
]
for _ in range(3):
    show_pattern(circle, 0.2)
    show_pattern([0b00000000]*8, 0.2)
clear()

# 5. Caminho em espiral
spiral = [
    0b11111111,
    0b10000001,
    0b10111101,
    0b10100101,
    0b10100101,
    0b10111101,
    0b10000001,
    0b11111111
]
for _ in range(2):
    show_pattern(spiral, 0.4)
    show_pattern([0b00000000]*8, 0.2)
clear()

# 6. Aleatório: "caminhando" na diagonal
for i in range(8):
    pattern = [0]*8
    pattern[i] = 1 << i
    show_pattern(pattern, 0.1)
clear()

# Fim: tudo aceso e tudo apagado
show_pattern([0xFF]*8, 0.5)
clear() 