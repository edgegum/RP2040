from machine import Pin, PWM, ADC, SPI, UART
import time
import framebuf
import math
import gc

# Display pins
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

class PWMPlotter:
    def __init__(self):
        self.adc28 = ADC(2)  # GPIO28
        self.lcd = LCD_1inch14()
        self.pwm = PWM(Pin(BL))
        self.pwm.freq(1000)
        self.pwm.duty_u16(32768)
        
        # Inicializa UART
        self.uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
        self.uart.init(baudrate=115200, bits=8, parity=None, stop=1)
        
        self.last_save = 0
        self.save_interval = 100  # ms
        
        # Buffer para o gráfico
        self.buffer_size = 100
        self.valores = [0] * self.buffer_size
        self.indice = 0
        
        # Desenha a grade
        self.lcd.fill(colour(0,0,0))
        self.lcd.line(20, 120, 220, 120, colour(255,255,255))  # Eixo X
        self.lcd.line(20, 20, 20, 120, colour(255,255,255))    # Eixo Y
        self.lcd.show()

    def salvar_dado(self, valor):
        """Salva um dado via UART"""
        timestamp = time.ticks_ms()
        self.uart.write(f"{timestamp},{valor}\n")

    def atualizar_display(self, valor):
        """Atualiza o display com o valor atual e o gráfico"""
        # Atualiza o buffer circular
        self.valores[self.indice] = valor
        self.indice = (self.indice + 1) % self.buffer_size
        
        # Limpa a área do gráfico
        self.lcd.fill_rect(21, 21, 199, 99, colour(0,0,0))
        
        # Desenha a grade
        self.lcd.line(20, 120, 220, 120, colour(255,255,255))  # Eixo X
        self.lcd.line(20, 20, 20, 120, colour(255,255,255))    # Eixo Y
        
        # Desenha o gráfico
        for i in range(self.buffer_size):
            x = 21 + i
            y = 120 - int((self.valores[i] / 65535) * 100)
            if 21 <= x <= 220 and 21 <= y <= 120:
                self.lcd.fill_rect(x, y, 1, 1, colour(0,255,0))
        
        # Mostra o valor atual
        self.lcd.text(f"ADC: {valor}", 10, 10, colour(255,255,255))
        
        # Atualiza o display
        self.lcd.show()

    def run(self):
        try:
            # Mensagem inicial
            self.lcd.fill(colour(0,0,0))
            self.lcd.text("PWM Plotter", 30, 60, colour(255,255,255))
            self.lcd.text("Iniciando...", 30, 80, colour(0,255,0))
            self.lcd.show()
            time.sleep_ms(1000)
            
            while True:
                # Lê o ADC
                valor = self.adc28.read_u16()
                
                # Atualiza o display
                self.atualizar_display(valor)
                
                # Salva dado a cada 100ms
                if time.ticks_diff(time.ticks_ms(), self.last_save) >= self.save_interval:
                    self.salvar_dado(valor)
                    self.last_save = time.ticks_ms()
                
                time.sleep_ms(50)  # Atualiza a cada 50ms
                
        except Exception as e:
            self.lcd.fill(colour(0,0,0))
            self.lcd.text(f"Erro: {str(e)}", 30, 60, colour(255,0,0))
            self.lcd.show()
            time.sleep_ms(5000)

def main():
    plotter = PWMPlotter()
    plotter.run()

if __name__ == "__main__":
    main() 