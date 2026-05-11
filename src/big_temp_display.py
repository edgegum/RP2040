from machine import Pin, SPI, PWM

import utime
import onewire
import ds18x20

# Pinos do display
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
        
        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(1)
        self.spi = SPI(1,1000_000)
        self.spi = SPI(1,100000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()
        
        self.red   =   0x07E0
        self.green =   0x001f
        self.blue  =   0xf800
        self.white =   0xffff
        
    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)  

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        self.rst(1)
        self.rst(0)
        self.rst(1)
        
        self.write_cmd(0x36)
        self.write_data(0x70)

        self.write_cmd(0x3A) 
        self.write_data(0x05)

        self.write_cmd(0xB2)
        self.write_data(0x0C)
        self.write_data(0x0C)
        self.write_data(0x00)
        self.write_data(0x33)
        self.write_data(0x33)

        self.write_cmd(0xB7)
        self.write_data(0x35) 

        self.write_cmd(0xBB)
        self.write_data(0x19)

        self.write_cmd(0xC0)
        self.write_data(0x2C)

        self.write_cmd(0xC2)
        self.write_data(0x01)

        self.write_cmd(0xC3)
        self.write_data(0x12)   

        self.write_cmd(0xC4)
        self.write_data(0x20)

        self.write_cmd(0xC6)
        self.write_data(0x0F) 

        self.write_cmd(0xD0)
        self.write_data(0xA4)
        self.write_data(0xA1)

        self.write_cmd(0xE0)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0D)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2B)
        self.write_data(0x3F)
        self.write_data(0x54)
        self.write_data(0x4C)
        self.write_data(0x18)
        self.write_data(0x0D)
        self.write_data(0x0B)
        self.write_data(0x1F)
        self.write_data(0x23)

        self.write_cmd(0xE1)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0C)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2C)
        self.write_data(0x3F)
        self.write_data(0x44)
        self.write_data(0x51)
        self.write_data(0x2F)
        self.write_data(0x1F)
        self.write_data(0x1F)
        self.write_data(0x20)
        self.write_data(0x23)
        
        self.write_cmd(0x21)

        self.write_cmd(0x11)

        self.write_cmd(0x29)

    def show(self):
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x28)
        self.write_data(0x01)
        self.write_data(0x17)
        
        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x35)
        self.write_data(0x00)
        self.write_data(0xBB)
        
        self.write_cmd(0x2C)
        
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)

def colour(R,G,B):
    return (((G&0b00011100)<<3) +((B&0b11111000)>>3)<<8) + (R&0b11111000)+((G&0b11100000)>>5)

# Inicialização do display
lcd = LCD_1inch14()
lcd.fill(colour(0,0,0))
lcd.show()

# Configuração do brilho
pwm = PWM(Pin(BL))
pwm.freq(1000)
pwm.duty_u16(32768)

# Configuração do DS18B20
ds_pin = Pin(28)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()

def draw_big_text(text, x, y, color, scale=2.76):  # Reduced scale by 8%
    """Desenha texto grande usando linhas e retângulos para formar os caracteres"""
    # Define os padrões de segmentos para cada dígito
    digit_patterns = {
        '0': [(0,0,15,3), (0,0,3,25), (12,0,3,25), (0,22,15,3)],  # (x,y,width,height)
        '1': [(5,0,5,25)],
        '2': [(0,0,15,3), (12,0,3,12), (0,12,15,3), (0,12,3,12), (0,22,15,3)],
        '3': [(0,0,15,3), (12,0,3,25), (0,12,15,3), (0,22,15,3)],
        '4': [(0,0,3,12), (0,12,15,3), (12,0,3,25)],
        '5': [(0,0,15,3), (0,0,3,12), (0,12,15,3), (12,12,3,12), (0,22,15,3)],
        '6': [(0,0,15,3), (0,0,3,25), (0,12,15,3), (12,12,3,12), (0,22,15,3)],
        '7': [(0,0,15,3), (12,0,3,25)],
        '8': [(0,0,15,3), (0,0,3,25), (12,0,3,25), (0,12,15,3), (0,22,15,3)],
        '9': [(0,0,15,3), (0,0,3,12), (12,0,3,25), (0,12,15,3), (0,22,15,3)]
    }
    
    for char in text:
        if char == '°':
            # Desenha o símbolo de grau igual ao ponto, mas na linha superior
            lcd.fill_rect(int(x + 3*scale), int(y), int(6*scale), int(6*scale), color)
            x += 15*scale
        elif char == '.':
            # Desenha o ponto decimal
            lcd.fill_rect(int(x + 3*scale), int(y + 15*scale), int(6*scale), int(6*scale), color)
            x += 15*scale
        elif char.isdigit():
            # Desenha os números usando os padrões definidos
            for pattern in digit_patterns[char]:
                lcd.fill_rect(int(x + pattern[0]*scale), int(y + pattern[1]*scale), 
                            int(pattern[2]*scale), int(pattern[3]*scale), color)
            x += 20*scale
        else:
            x += 8*scale

def update_display(temp):
    lcd.fill(colour(0,0,0))  # Limpa o display
    
    if temp is not None:
        # Formata a temperatura com um decimal
        temp_str = f"{temp:.1f}°"
        
        # Calcula a posição central e desloca 10% para a direita
        text_width = int(len(temp_str) * 20 * 2.76)  # Convertido para inteiro
        x = int((240 - text_width) // 2 + (240 * 0.1))  # Adiciona 10% de deslocamento para direita
        y = 20  # Posição vertical mais alta
        
        # Desenha a temperatura em caracteres grandes
        draw_big_text(temp_str, x, y, colour(0,255,0))
    else:
        # Mensagem de erro em texto grande
        draw_big_text("ERRO", int(40 + (240 * 0.1)), 20, colour(255,0,0))  # Também desloca a mensagem de erro
        lcd.text("Verifique conexoes", int(40 + (240 * 0.1)), 80, colour(255,0,0))
    
    lcd.show()

# Loop principal
print("Iniciando display de temperatura...")
print("Pressione Ctrl+C para sair")

try:
    while True:
        # Lê a temperatura
        ds_sensor.convert_temp()
        utime.sleep_ms(750)
        temp = ds_sensor.read_temp(roms[0]) if roms else None
        
        # Atualiza o display
        update_display(temp)
        
        # Mostra também no console
        print(f"Temperatura: {temp:.1f}°C" if temp is not None else "Erro na leitura")
        
        # Aguarda 2 segundos
        utime.sleep_ms(2000)

except KeyboardInterrupt:
    print("\nPrograma finalizado")
except Exception as e:
    print("Erro:", e)
finally:
    lcd.fill(colour(0,0,0))  # Limpa o display ao finalizar
    lcd.show() 