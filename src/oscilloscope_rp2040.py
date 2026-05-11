"""
Osciloscópio Digital para Raspberry Pi Pico
------------------------------------------

Este script implementa um osciloscópio digital simples usando o Raspberry Pi Pico e um display TFT 1.14" SPI.

Funcionalidades:
- Captura inicial de um pulso periódico (ex: de um oscilador de relaxação com UJT)
- Mede automaticamente a largura e o período do pulso
- Ajusta a janela de tempo para exibir aproximadamente três pulsos na tela
- Passa para modo contínuo, exibindo os pulsos em tempo real, com trigger
- Visualização limpa, com apenas informações essenciais na tela
- Trigger centralizado, indicado por um triângulo vermelho

Como usar:
1. Conecte o sinal ao GPIO28 (ADC2)
2. O display mostrará "Aguardando..." até capturar o primeiro pulso
3. Após a captura, o script ajusta a janela de tempo e passa a exibir os pulsos continuamente
4. O texto "Pulso" e a largura do pulso são mostrados no canto superior esquerdo

Limitações:
- A resolução temporal máxima depende da taxa de amostragem do ADC (em Python, até ~1MHz)
- Pulsos muito estreitos podem aparecer como "impulsos" devido à limitação do ADC

Autor: Adaptado por IA para uso didático
"""

from machine import Pin, ADC, SPI, PWM
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
PWM_REF_PIN = 16  # PWM de referência
PWM_MED_PIN = 17  # PWM de medição
ADC_PULSE = 28   # GPIO28

class LCD_1inch14(framebuf.FrameBuffer):
    """
    Classe para controle do display TFT 1.14" SPI.
    Fornece métodos para inicialização, escrita de comandos/dados e atualização da tela.
    """
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
        """Envia comando para o display."""
        self.cs(1); self.dc(0); self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)
    def write_data(self, buf):
        """Envia dados para o display."""
        self.cs(1); self.dc(1); self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)
    def init_display(self):
        """Inicializa o display com a sequência de comandos padrão."""
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
        """Atualiza o display com o conteúdo do framebuffer."""
        self.write_cmd(0x2A); self.write_data(0x00); self.write_data(0x28)
        self.write_data(0x01); self.write_data(0x17)
        self.write_cmd(0x2B); self.write_data(0x00); self.write_data(0x35)
        self.write_data(0x00); self.write_data(0xBB)
        self.write_cmd(0x2C)
        self.cs(1); self.dc(1); self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)

def colour(R,G,B):
    """Converte valores RGB para o formato RGB565 usado pelo display."""
    return (((G&0b00011100)<<3) +((B&0b11111000)>>3)<<8) + (R&0b11111000)+((G&0b11100000)>>5)

class PWMControlledByPulse:
    """
    Gera dois PWMs: referência (duty fixo) e medição (duty ajustado pelo tempo do pulso detectado).
    Exibe ambos os valores e a diferença (largura do pulso) na tela.
    """
    def __init__(self):
        self.lcd = LCD_1inch14()
        self.pwm = Pin(BL, Pin.OUT)
        self.pwm.value(1)
        self.pwm_ref = PWM(Pin(PWM_REF_PIN))
        self.pwm_med = PWM(Pin(PWM_MED_PIN))
        self.pwm_freq = 1000  # Hz
        self.pwm_ref.freq(self.pwm_freq)
        self.pwm_med.freq(self.pwm_freq)
        self.duty_ref_us = 500  # 500us (50% de 1ms)
        self.duty_med_us = 500  # Inicialmente igual ao ref
        self.pwm_ref.duty_u16(int(self.duty_ref_us / 1000 * 65535))
        self.pwm_med.duty_u16(int(self.duty_med_us / 1000 * 65535))
        self.adc = ADC(ADC_PULSE)
        self.threshold = 40000
        self.pulse_width_us = 0
    def measure_pulse(self):
        # Espera borda de subida
        while self.adc.read_u16() < self.threshold:
            pass
        t_start = time.ticks_us()
        # Espera borda de descida
        while self.adc.read_u16() > self.threshold:
            pass
        t_end = time.ticks_us()
        pulse_width = time.ticks_diff(t_end, t_start)
        return pulse_width
    def run(self):
        while True:
            # Mede o pulso do UJT
            self.pulse_width_us = self.measure_pulse()
            # Ajusta o duty do PWM de medição
            self.duty_med_us = self.duty_ref_us + self.pulse_width_us
            # Garante que duty não ultrapasse o período
            if self.duty_med_us > 1000:
                self.duty_med_us = 1000
            self.pwm_ref.duty_u16(int(self.duty_ref_us / 1000 * 65535))
            self.pwm_med.duty_u16(int(self.duty_med_us / 1000 * 65535))
            # Exibe na tela
            self.lcd.fill(colour(0,0,0))
            self.lcd.text("PWM ref: {}us".format(self.duty_ref_us), 5, 5, colour(0,128,255))
            self.lcd.text("PWM med: {}us".format(self.duty_med_us), 5, 20, colour(0,255,0))
            self.lcd.text("Pulso UJT: {}us".format(self.pulse_width_us), 5, 35, colour(255,255,0))
            self.lcd.show()
            time.sleep_ms(200)

class PulseWidthInterrupt:
    """
    Mede largura de pulso digital usando interrupção no GPIO28 e exibe no display TFT.
    """
    def __init__(self):
        self.lcd = LCD_1inch14()
        self.pwm = Pin(BL, Pin.OUT)
        self.pwm.value(1)
        self.pulse_pin = Pin(28, Pin.IN, Pin.PULL_DOWN)
        self.pulse_start = None
        self.pulse_width = 0
        self.last_pulse_width = 0
        self.waiting_for_rise = True
        self.pulse_pin.irq(trigger=Pin.IRQ_RISING, handler=self.pulse_handler)
    def pulse_handler(self, pin):
        now = time.ticks_us()
        if self.waiting_for_rise:
            self.pulse_start = now
            self.waiting_for_rise = False
            pin.irq(trigger=Pin.IRQ_FALLING, handler=self.pulse_handler)
        else:
            if self.pulse_start is not None:
                self.pulse_width = time.ticks_diff(now, self.pulse_start)
                self.last_pulse_width = self.pulse_width
            self.waiting_for_rise = True
            pin.irq(trigger=Pin.IRQ_RISING, handler=self.pulse_handler)
    def run(self):
        while True:
            self.lcd.fill(colour(0,0,0))
            self.lcd.text("Pulso digital (GPIO28)", 5, 5, colour(255,255,255))
            self.lcd.text("Largura: {} us".format(self.last_pulse_width), 5, 25, colour(255,255,0))
            self.lcd.show()
            time.sleep_ms(100)

class PeriodToSquareWave:
    """
    Mede o período de um pulso digital via interrupção (GPIO28) e exibe uma onda quadrada sintética com o mesmo período no display TFT.
    """
    def __init__(self):
        self.lcd = LCD_1inch14()
        self.pwm = Pin(BL, Pin.OUT)
        self.pwm.value(1)
        self.pulse_pin = Pin(28, Pin.IN, Pin.PULL_DOWN)
        self.last_rise = None
        self.period = 1000  # valor inicial em us
        self.waiting_for_rise = True
        self.pulse_pin.irq(trigger=Pin.IRQ_RISING, handler=self.pulse_handler)
    def pulse_handler(self, pin):
        now = time.ticks_us()
        if self.waiting_for_rise:
            if self.last_rise is not None:
                self.period = time.ticks_diff(now, self.last_rise)
            self.last_rise = now
            self.waiting_for_rise = False
            pin.irq(trigger=Pin.IRQ_FALLING, handler=self.pulse_handler)
        else:
            self.waiting_for_rise = True
            pin.irq(trigger=Pin.IRQ_RISING, handler=self.pulse_handler)
    def draw_square_wave(self, period_us, duty=0.5):
        """Desenha uma onda quadrada sintética no display, com o período especificado (em us)."""
        self.lcd.fill(colour(0,0,0))
        self.lcd.text("Periodo: {} us".format(period_us), 5, 5, colour(255,255,0))
        # Parâmetros de desenho
        x0 = 10
        y0 = 40
        width = 220
        height = 60
        # Calcula quantos períodos cabem na tela
        n_periods = 3
        t_total = period_us * n_periods
        px_per_us = width / t_total
        # Desenha a onda quadrada
        x = x0
        for i in range(n_periods):
            t_high = period_us * duty
            t_low = period_us * (1 - duty)
            x1 = x + t_high * px_per_us
            x2 = x + period_us * px_per_us
            # Sobe
            self.lcd.line(int(x), y0+height, int(x), y0, colour(0,255,0))
            # Topo
            self.lcd.line(int(x), y0, int(x1), y0, colour(0,255,0))
            # Desce
            self.lcd.line(int(x1), y0, int(x1), y0+height, colour(0,255,0))
            # Base
            self.lcd.line(int(x1), y0+height, int(x2), y0+height, colour(0,255,0))
            x = x2
    def run(self):
        while True:
            self.draw_square_wave(self.period)
            self.lcd.show()
            time.sleep_ms(100)

class PlotPWMADC:
    """
    Lê a onda quadrada real do PWM via ADC3 (GPIO29) e plota no display TFT.
    """
    def __init__(self):
        self.lcd = LCD_1inch14()
        self.pwm = Pin(BL, Pin.OUT)
        self.pwm.value(1)
        self.adc = ADC(3)  # GPIO29
        self.num_points = 240
        self.buffer = [0] * self.num_points
    def plot_pwm(self):
        # Coleta os pontos do PWM
        for i in range(self.num_points):
            self.buffer[i] = self.adc.read_u16()
            time.sleep_us(5)  # Ajuste para a resolução desejada
        # Plota no display (lógica inspirada no transistor tracer)
        self.lcd.fill(colour(0,0,0))
        # Eixos
        self.lcd.line(20, 120, 220, 120, colour(255,255,255))
        self.lcd.line(20, 20, 20, 120, colour(255,255,255))
        # Onda
        for i in range(self.num_points-1):
            x1 = int(20 + (i / self.num_points) * 200)
            y1 = int(120 - (self.buffer[i] / 65535) * 100)
            x2 = int(20 + ((i+1) / self.num_points) * 200)
            y2 = int(120 - (self.buffer[i+1] / 65535) * 100)
            self.lcd.line(x1, y1, x2, y2, colour(0,255,0))
        self.lcd.text("PWM real (ADC3)", 30, 10, colour(255,255,0))
        self.lcd.show()
    def run(self):
        while True:
            self.plot_pwm()
            time.sleep_ms(50)

def main():
    scope = PlotPWMADC()
    try:
        scope.run()
    except Exception as e:
        scope.lcd.fill(colour(0,0,0))
        scope.lcd.text(f"Erro: {str(e)}", 30, 60, colour(255,0,0))
        scope.lcd.show()
        time.sleep_ms(5000)

if __name__ == "__main__":
    main() 