from machine import Pin, PWM, ADC, SPI
import time
import framebuf
import math
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
        gc.collect()  # Libera memória antes de criar o framebuffer
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

class Oscilloscope:
    def __init__(self):
        self.gpio2 = Pin(2, Pin.OUT)
        self.gpio3 = Pin(3, Pin.OUT)
        self.adc28 = ADC(28)
        self.adc29 = ADC(29)
        self.pwm2 = PWM(self.gpio2)
        self.pwm3 = PWM(self.gpio3)
        self.pwm2.freq(1000)
        self.pwm3.freq(1000)
        self.lcd = LCD_1inch14()
        self.pwm = PWM(Pin(BL))
        self.pwm.freq(1000)
        self.pwm.duty_u16(32768)
    def simular_transistor(self):
        Vce_sat = 0.2
        beta = 200
        base_currents = [10, 30, 50]  # Menos curvas
        vce_steps = 40  # Menos pontos
        cores = [colour(255,0,0), colour(0,255,0), colour(0,0,255)]
        self.lcd.fill(colour(0,0,0))
        self.lcd.line(20, 120, 220, 120, colour(255,255,255))
        self.lcd.line(20, 20, 20, 120, colour(255,255,255))
        self.lcd.show()
        for idx, ib in enumerate(base_currents):
            cor = cores[idx % len(cores)]
            ib_amp = ib * 1e-6
            for i in range(vce_steps):
                vce_voltage = (i / vce_steps) * 3.3
                ic = beta * ib_amp * (vce_voltage / Vce_sat) if vce_voltage < Vce_sat else beta * ib_amp * (1 + vce_voltage / 100)
                ic = min(ic, 0.1)
                self.pwm2.duty_u16(int(vce_voltage * 65535 / 3.3))
                self.pwm3.duty_u16(int(ic * 65535 / 0.1))
                time.sleep_ms(30)
                vce_reading = self.adc28.read_u16() * 3.3 / 65535
                ic_reading = self.adc29.read_u16() * 3.3 / 65535
                x = int(20 + (vce_reading / 3.3) * 200)
                y = int(120 - (ic_reading / 0.1) * 100)
                self.lcd.fill_rect(x, y, 2, 2, cor)
                if i % 5 == 0:
        self.lcd.show()
            self.lcd.show()
            time.sleep_ms(300)
        self.pwm2.duty_u16(0)
        self.pwm3.duty_u16(0)
        self.lcd.fill(colour(0,0,0))
        self.lcd.text("Simulacao BC548", 30, 60, colour(255,255,255))
        self.lcd.text("Completa!", 30, 80, colour(0,255,0))
        self.lcd.show()
        time.sleep_ms(1000)

def main():
    scope = Oscilloscope()
    try:
        scope.simular_transistor()
        time.sleep_ms(2000)
    except Exception as e:
        scope.lcd.fill(colour(0,0,0))
        scope.lcd.text(f"Erro: {str(e)}", 30, 60, colour(255,0,0))
        scope.lcd.show()
        time.sleep_ms(5000)
    finally:
        scope.pwm2.duty_u16(0)
        scope.pwm3.duty_u16(0)

if __name__ == "__main__":
    main() 