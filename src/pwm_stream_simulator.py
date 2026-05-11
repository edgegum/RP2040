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

def colour(R,G,B):
    return (((G&0b00011100)<<3) +((B&0b11111000)>>3)<<8) + (R&0b11111000)+((G&0b11100000)>>5)

class DualPWMDemo:
    def __init__(self):
        self.pwm1 = PWM(Pin(2, Pin.OUT))
        self.pwm2 = PWM(Pin(3, Pin.OUT))
        self.adc1 = ADC(2)  # GPIO28
        self.adc2 = ADC(1)  # GPIO27
        self.pwm1.freq(50)
        self.pwm2.freq(50)
        self.lcd = LCD_1inch14()
        self.lcd.fill(colour(0,0,0))
        self.lcd.show()

    def run(self):
        steps = 200
        delay = 40  # ms
        while True:
            # PWM1 sobe de 0% a 100%, PWM2 em 0%
            for i in range(steps):
                duty1 = int((i/steps)*65535)
                self.pwm1.duty_u16(duty1)
                self.pwm2.duty_u16(0)
                time.sleep_ms(delay)
                val1 = self.adc1.read_u16() * 3.3 / 65535
                val2 = self.adc2.read_u16() * 3.3 / 65535
                self.display(val1, val2, "PWM1 variando")
            # PWM2 sobe de 0% a 100%, PWM1 em 0%
            for i in range(steps):
                duty2 = int((i/steps)*65535)
                self.pwm1.duty_u16(0)
                self.pwm2.duty_u16(duty2)
                time.sleep_ms(delay)
                val1 = self.adc1.read_u16() * 3.3 / 65535
                val2 = self.adc2.read_u16() * 3.3 / 65535
                self.display(val1, val2, "PWM2 variando")

    def display(self, val1, val2, status):
        self.lcd.fill(colour(0,0,0))
        self.lcd.text(f"PWM1: {val1:.2f}V", 10, 20, colour(0,255,0))
        self.lcd.text(f"PWM2: {val2:.2f}V", 10, 40, colour(0,0,255))
        self.lcd.text(status, 10, 60, colour(255,255,0))
        bar1 = int((val1/3.3)*200)
        bar2 = int((val2/3.3)*200)
        self.lcd.fill_rect(20, 90, bar1, 10, colour(0,255,0))
        self.lcd.fill_rect(20, 110, bar2, 10, colour(0,0,255))
        self.lcd.show()

def main():
    demo = DualPWMDemo()
    demo.run()

if __name__ == "__main__":
    main() 