from machine import Pin, PWM, ADC, SPI
import time
import framebuf
import gc

BL = 13
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

def colour(R,G,B):
    return (((G&0b00011100)<<3) +((B&0b11111000)>>3)<<8) + (R&0b11111000)+((G&0b11100000)>>5)

class LCD_1inch14(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 240
        self.height = 135
        gc.collect()
        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        self.cs(1)
        self.spi = SPI(1,100000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()
    def write_cmd(self, cmd):
        self.cs(1); self.dc(0); self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)
    def write_data(self, buf):
        self.cs(1); self.dc(1); self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)
    def init_display(self):
        for cmd, data in [
            (0x36, [0x70]), (0x3A, [0x05]), (0xB2, [0x0C,0x0C,0x00,0x33,0x33]),
            (0xB7, [0x35]), (0xBB, [0x19]), (0xC0, [0x2C]), (0xC2, [0x01]),
            (0xC3, [0x12]), (0xC4, [0x20]), (0xC6, [0x0F]), (0xD0, [0xA4,0xA1]),
            (0xE0, [0xD0,0x04,0x0D,0x11,0x13,0x2B,0x3F,0x54,0x4C,0x18,0x0D,0x0B,0x1F,0x23]),
            (0xE1, [0xD0,0x04,0x0C,0x11,0x13,0x2C,0x3F,0x44,0x51,0x2F,0x1F,0x1F,0x20,0x23]),
            (0x21, []), (0x11, []), (0x29, [])
        ]:
            self.write_cmd(cmd)
            for d in data: self.write_data(d)
    def show(self):
        self.write_cmd(0x2A); self.write_data(0x00); self.write_data(0x28)
        self.write_data(0x01); self.write_data(0x17)
        self.write_cmd(0x2B); self.write_data(0x00); self.write_data(0x35)
        self.write_data(0x00); self.write_data(0xBB)
        self.write_cmd(0x2C)
        self.cs(1); self.dc(1); self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)

def main():
    lcd = LCD_1inch14()
    adc0 = ADC(0)  # GPIO26
    adc1 = ADC(1)  # GPIO27
    adc2 = ADC(2)  # GPIO28
    pwm1 = PWM(Pin(2, Pin.OUT))
    pwm2 = PWM(Pin(3, Pin.OUT))
    pwm1.freq(50)
    pwm2.freq(50)
    steps = 100
    while True:
        # PWM1 sobe, PWM2 desce
        for i in range(steps):
            duty1 = int((i/steps)*65535)
            duty2 = int(((steps-1-i)/steps)*65535)
            pwm1.duty_u16(duty1)
            pwm2.duty_u16(duty2)
            v0 = adc0.read_u16() * 3.3 / 65535
            v1 = adc1.read_u16() * 3.3 / 65535
            v2 = adc2.read_u16() * 3.3 / 65535
            lcd.fill(colour(0,0,0))
            lcd.text(f"ADC0 (GPIO26): {v0:.2f}V", 10, 20, colour(255,255,0))
            lcd.text(f"ADC1 (GPIO27): {v1:.2f}V", 10, 40, colour(0,255,255))
            lcd.text(f"ADC2 (GPIO28): {v2:.2f}V", 10, 60, colour(255,0,255))
            lcd.text(f"PWM1: {duty1//655:.0f}%", 10, 90, colour(0,255,0))
            lcd.text(f"PWM2: {duty2//655:.0f}%", 10, 110, colour(0,0,255))
            lcd.show()
            time.sleep_ms(40)

if __name__ == "__main__":
    main() 