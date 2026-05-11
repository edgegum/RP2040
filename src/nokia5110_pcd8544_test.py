"""
Teste do Display LCD Nokia 5110 com Controlador PCD8544
=======================================================

Este script testa um display LCD Nokia 5110 usando o controlador PCD8544
através de comunicação SPI. Segue a mesma estrutura do script matrix8x8_bitbang.py.

Hardware necessário:
- Display LCD Nokia 5110 (84x48 pixels)
- Controlador PCD8544
- Raspberry Pi Pico ou similar

Conexões:
- RST: Pino 29 (Reset)
- CE:  Pino 28 (Chip Enable)
- DC:  Pino 5  (Data/Command)
- DIN: Pino 4  (Data In)
- CLK: Pino 3  (Clock)
- VCC: 3.3V
- GND: GND

Nota: Usando apenas os GPIOs disponíveis no seu RP2040

Autor: Baseado na estrutura de matrix8x8_bitbang.py
"""

from machine import Pin, SPI
import time
import framebuf

# Configuração dos pinos para Nokia 5110 (PCD8544)
# Usando apenas os GPIOs disponíveis: 29, 28, 5, 4, 3, 2
RST = Pin(29, Pin.OUT)  # Reset
CE  = Pin(28, Pin.OUT)  # Chip Enable  
DC  = Pin(5,  Pin.OUT)  # Data/Command
DIN = Pin(4,  Pin.OUT)  # Data In
CLK = Pin(3,  Pin.OUT)  # Clock

# Configuração do SPI para comunicação com PCD8544
spi = SPI(0, baudrate=1000000, polarity=0, phase=0, sck=CLK, mosi=DIN)

# Dimensões do display Nokia 5110
LCD_WIDTH = 84
LCD_HEIGHT = 48
LCD_ROWS = 6  # 48/8 = 6 linhas de 8 bits cada

class Nokia5110:
    def __init__(self, spi, rst, ce, dc):
        self.spi = spi
        self.rst = rst
        self.ce = ce
        self.dc = dc
        
        # Buffer de frame
        self.buffer = bytearray(LCD_WIDTH * LCD_ROWS)
        self.framebuf = framebuf.FrameBuffer(self.buffer, LCD_WIDTH, LCD_HEIGHT, framebuf.MONO_VLSB)
        
        self.init_display()
    
    def init_display(self):
        """Inicializa o display PCD8544"""
        self.rst.off()
        time.sleep_ms(100)
        self.rst.on()
        time.sleep_ms(100)
        
        # Sequência de inicialização do PCD8544
        self.write_cmd(0x21)  # Extended instruction set
        self.write_cmd(0xBF)  # Set VOP (contraste)
        self.write_cmd(0x04)  # Set temp coefficient
        self.write_cmd(0x14)  # Set bias mode
        self.write_cmd(0x20)  # Basic instruction set
        self.write_cmd(0x0C)  # Normal display mode
        
        # Limpa o display
        self.clear()
    
    def write_cmd(self, cmd):
        """Escreve comando no display"""
        self.dc.off()  # Modo comando
        self.ce.off()
        self.spi.write(bytes([cmd]))
        self.ce.on()
    
    def write_data(self, data):
        """Escreve dados no display"""
        self.dc.on()   # Modo dados
        self.ce.off()
        self.spi.write(data)
        self.ce.on()
    
    def clear(self):
        """Limpa o display"""
        for i in range(LCD_WIDTH * LCD_ROWS):
            self.buffer[i] = 0
        self.update()
    
    def update(self):
        """Atualiza o display com o conteúdo do buffer"""
        for row in range(LCD_ROWS):
            self.write_cmd(0x80)  # Set X address
            self.write_cmd(0x40 + row)  # Set Y address
            start = row * LCD_WIDTH
            end = start + LCD_WIDTH
            self.write_data(self.buffer[start:end])
    
    def show_text(self, text, x=0, y=0, color=1):
        """Mostra texto no display"""
        self.framebuf.text(text, x, y, color)
        self.update()
    
    def draw_rect(self, x, y, w, h, color=1):
        """Desenha um retângulo"""
        self.framebuf.rect(x, y, w, h, color)
        self.update()
    
    def fill_rect(self, x, y, w, h, color=1):
        """Preenche um retângulo"""
        self.framebuf.fill_rect(x, y, w, h, color)
        self.update()
    
    def draw_circle(self, x, y, r, color=1):
        """Desenha um círculo"""
        self.framebuf.ellipse(x, y, r, r, color)
        self.update()
    
    def draw_line(self, x1, y1, x2, y2, color=1):
        """Desenha uma linha"""
        self.framebuf.line(x1, y1, x2, y2, color)
        self.update()
    
    def show_pattern(self, pattern, delay=0.2):
        """Mostra um padrão específico no display"""
        self.clear()
        # Aqui você pode implementar padrões específicos
        # Por exemplo, mostrar um bitmap ou padrão customizado
        self.update()
        time.sleep(delay)

# Inicializa o display
lcd = Nokia5110(spi, RST, CE, DC)

# 1. Teste de inicialização - Limpa o display
lcd.clear()
time.sleep(1)

# 2. Teste de texto básico
lcd.show_text("Nokia 5110", 0, 0)
lcd.show_text("PCD8544", 0, 8)
lcd.show_text("Test OK!", 0, 16)
time.sleep(2)

# 3. Teste de retângulos
lcd.clear()
lcd.draw_rect(10, 10, 20, 15, 1)
lcd.show_text("Rect", 12, 12)
time.sleep(1)

lcd.fill_rect(40, 10, 20, 15, 1)
lcd.show_text("Fill", 42, 12, 0)  # Texto branco sobre fundo preto
time.sleep(1)

# 4. Teste de círculos
lcd.clear()
lcd.draw_circle(20, 20, 8, 1)
lcd.show_text("Circle", 30, 16)
time.sleep(1)

lcd.draw_circle(60, 20, 8, 1)
lcd.fill_rect(55, 15, 10, 10, 1)  # Preenche o círculo
time.sleep(1)

# 5. Teste de linhas diagonais
lcd.clear()
lcd.draw_line(0, 0, 83, 47, 1)
lcd.draw_line(83, 0, 0, 47, 1)
lcd.show_text("Lines", 30, 20)
time.sleep(1)

# 6. Padrão de grade (grid)
lcd.clear()
for i in range(0, 84, 8):
    lcd.draw_line(i, 0, i, 47, 1)
for i in range(0, 48, 8):
    lcd.draw_line(0, i, 83, i, 1)
lcd.show_text("Grid", 30, 20)
time.sleep(1)

# 7. Animação simples - quadrado se movendo
lcd.clear()
for i in range(0, 60, 4):
    lcd.fill_rect(i, 20, 8, 8, 1)
    time.sleep(0.1)
    lcd.fill_rect(i, 20, 8, 8, 0)  # Apaga
lcd.fill_rect(60, 20, 8, 8, 1)  # Deixa no final

# 8. Padrão de bordas - moldura
lcd.clear()
lcd.draw_rect(0, 0, 84, 48, 1)
lcd.draw_rect(5, 5, 74, 38, 1)
lcd.show_text("BORDAS", 25, 20)
time.sleep(1)

# 9. Teste de contraste - texto piscando
for _ in range(3):
    lcd.show_text("BLINK", 25, 20)
    time.sleep(0.5)
    lcd.show_text("     ", 25, 20)  # Espaços para "apagar"
    time.sleep(0.5)

# 10. Teste final - mensagem de conclusão
lcd.clear()
lcd.show_text("Teste", 25, 0)
lcd.show_text("Nokia 5110", 15, 8)
lcd.show_text("Concluido!", 20, 16)
lcd.show_text("PCD8544 OK", 18, 24)
lcd.show_text(":)", 35, 32)

# Desenha uma moldura
lcd.draw_rect(0, 0, 84, 48, 1)

print("Teste do display Nokia 5110 concluído!") 