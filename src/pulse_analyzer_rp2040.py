from machine import Pin, PWM, ADC, SPI
import time
import framebuf
import gc

# Display pins
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

class PulseAnalyzer:
    def __init__(self):
        # Display setup
        self.lcd = LCD_1inch14()
        self.pwm = Pin(BL, Pin.OUT)
        self.pwm.value(1)
        
        # Input measurement via interrupt
        self.pulse_pin = Pin(28, Pin.IN, Pin.PULL_DOWN)
        self.rise_time = None
        
        # Buffers para média móvel
        self.num_samples = 10  # Número de amostras para média
        self.pulse_width_buffer = [0] * self.num_samples
        self.period_buffer = [0] * self.num_samples
        self.buffer_idx = 0
        self.pulse_width_us = 0
        self.period_us = 0
        
        # Detecção de mudanças
        self.last_width = 0
        self.width_change_count = 0
        self.is_stable = False
        
        # Inicializa interrupção
        self.pulse_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.pulse_handler)
        
        # PWM output
        self.pwm_out = PWM(Pin(16))
        self.pwm_out.freq(8)
        self.pwm_out.duty_u16(32768)
        
        # Display buffer for waveform
        self.num_points = 240
        self.display_buffer = [0] * self.num_points
        self.display_idx = 0

    def update_moving_average(self, new_width):
        """Atualiza a média móvel com novas medições."""
        # Verifica mudança significativa
        if self.last_width > 0:
            change = abs(new_width - self.last_width) / self.last_width
            if change > 0.1:  # Mudança maior que 10%
                self.width_change_count += 1
                if self.width_change_count >= 3:  # 3 mudanças consecutivas
                    self.is_stable = False
                    self.width_change_count = 0
                    # Limpa buffer para nova média
                    self.pulse_width_buffer = [0] * self.num_samples
                    self.buffer_idx = 0
                    self.pulse_width_us = 0
            else:
                self.width_change_count = 0
        
        self.last_width = new_width
        
        # Atualiza buffer
        self.pulse_width_buffer[self.buffer_idx] = new_width
        self.buffer_idx = (self.buffer_idx + 1) % self.num_samples
        
        # Calcula média
        valid_widths = [w for w in self.pulse_width_buffer if w > 0]
        if valid_widths:
            mean_width = sum(valid_widths) / len(valid_widths)
            filtered_widths = [w for w in valid_widths if abs(w - mean_width) < mean_width * 0.2]
            if filtered_widths:
                self.pulse_width_us = sum(filtered_widths) / len(filtered_widths)
                self.is_stable = True
                
                # Atualiza PWM com valores filtrados
                try:
                    if self.period_us > 0:
                        freq = int(1_000_000 / self.period_us)
                        if freq >= 1:
                            self.pwm_out.freq(freq)
                            duty = int((self.pulse_width_us / self.period_us) * 65535)
                            self.pwm_out.duty_u16(duty)
                except:
                    pass

    def pulse_handler(self, pin):
        now = time.ticks_us()
        if not pin.value():  # Falling edge (transição para 0V)
            if self.rise_time is not None:
                new_period = time.ticks_diff(now, self.rise_time)
                # Atualiza período independentemente
                self.period_us = new_period
            self.rise_time = now
        else:  # Rising edge (transição para 3.3V)
            if self.rise_time is not None:
                new_width = time.ticks_diff(now, self.rise_time)
                # Atualiza largura e aplica filtro
                self.update_moving_average(new_width)

    def draw_grid(self):
        """Desenha a grade de fundo."""
        graph_height = 90  # 2/3 de 135
        for x in range(0, 240, 40):
            self.lcd.line(x, 0, x, graph_height, colour(40,40,40))
        for y in range(0, graph_height, 15):
            self.lcd.line(0, y, 240, y, colour(40,40,40))

    def draw_info(self):
        """Desenha as informações de medição."""
        # Limpa área de texto
        self.lcd.fill_rect(0, 90, 240, 45, colour(0,0,0))
        
        # Largura do pulso (esquerda)
        if self.is_stable:
            self.lcd.text(f"Largura: {self.pulse_width_us/1000:.3f}ms", 10, 95, colour(255,255,255))
            # Frequência (direita)
            freq = 1_000_000 / self.period_us if self.period_us > 0 else 0
            self.lcd.text(f"Freq: {freq:.1f}Hz", 140, 95, colour(255,255,255))
            # Período (abaixo)
            self.lcd.text(f"Periodo: {self.period_us/1000:.3f}ms", 10, 110, colour(255,255,255))
        else:
            self.lcd.text("Ajustando...", 10, 95, colour(255,255,0))

    def draw_pulse(self, value):
        """Desenha o pulso na tela com efeito de scroll."""
        # Limpa a área do gráfico
        self.lcd.fill_rect(0, 0, 240, 90, colour(0,0,0))
        
        # Desenha a grade
        self.draw_grid()
        
        # Calcula a posição Y (invertida porque 0 está no topo)
        y = int(45 - (value * 45))  # 45 é a metade da altura do gráfico
        
        # Desenha o pulso
        self.lcd.line(0, y, 240, y, colour(0,255,0))
        
        # Desenha as informações
        self.draw_info()
        
        # Atualiza o display
        self.lcd.show()

    def run(self):
        while True:
            try:
                # Atualiza buffer de exibição
                self.display_buffer[self.display_idx] = (not self.pulse_pin.value()) * 65535
                self.display_idx = (self.display_idx + 1) % self.num_points
                
                # Atualiza display
                self.lcd.fill(colour(0,0,0))
                self.draw_grid()
                
                # Plota a forma de onda
                for i in range(self.num_points-1):
                    x1 = int(i * 240 / self.num_points)
                    y1 = int(90 - (self.display_buffer[i] / 65535) * 90)
                    x2 = int((i+1) * 240 / self.num_points)
                    y2 = int(90 - (self.display_buffer[i+1] / 65535) * 90)
                    self.lcd.line(x1, y1, x2, y2, colour(0,255,0))
                
                # Área de informações
                self.draw_info()
                
                self.lcd.show()
                time.sleep_ms(10)
                
            except Exception as e:
                print(f"Erro no loop principal: {e}")
                time.sleep_ms(1000)

def main():
    analyzer = PulseAnalyzer()
    try:
        analyzer.run()
    except Exception as e:
        analyzer.lcd.fill(colour(0,0,0))
        analyzer.lcd.text(f"Erro: {str(e)}", 30, 60, colour(255,0,0))
        analyzer.lcd.show()
        time.sleep_ms(5000)

if __name__ == "__main__":
    main() 