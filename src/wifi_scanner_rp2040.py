import network
import time
from machine import Pin, SPI
import framebuf

# Configuração do display
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

class WiFiScanner:
    def __init__(self):
        # Inicializa o display
        self.lcd = LCD_1inch14()
        self.pwm = PWM(Pin(BL))
        self.pwm.freq(1000)
        self.pwm.duty_u16(32768)
        
        # Inicializa o WiFi em modo station
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
    def scan_networks(self):
        """Escaneia redes WiFi próximas"""
        return self.wlan.scan()
    
    def draw_network_info(self, networks):
        """Desenha informações das redes no display"""
        # Limpa o display
        self.lcd.fill(colour(0,0,0))
        
        # Título
        self.lcd.text("WiFi Scanner", 10, 5, colour(255,255,255))
        self.lcd.text("RSSI (dBm)", 10, 20, colour(255,255,255))
        
        # Desenha as barras de sinal
        max_networks = 5  # Número máximo de redes a mostrar
        bar_width = 200
        bar_height = 15
        spacing = 20
        
        for i, (ssid, bssid, channel, rssi, authmode, hidden) in enumerate(networks[:max_networks]):
            # Calcula a largura da barra baseada no RSSI
            # RSSI típico varia de -100 (fraco) a -30 (forte)
            signal_strength = min(100, max(0, (rssi + 100) * 2))  # Converte para 0-100
            bar_length = int((signal_strength / 100) * bar_width)
            
            # Posição Y para esta rede
            y_pos = 40 + (i * spacing)
            
            # Nome da rede (truncado se necessário)
            ssid_str = ssid.decode('utf-8')[:15]  # Limita a 15 caracteres
            self.lcd.text(ssid_str, 10, y_pos, colour(255,255,255))
            
            # Barra de sinal
            self.lcd.fill_rect(10, y_pos + 10, bar_length, bar_height, colour(0,255,0))
            self.lcd.rect(10, y_pos + 10, bar_width, bar_height, colour(255,255,255))
            
            # Valor do RSSI
            self.lcd.text(f"{rssi} dBm", bar_width + 20, y_pos + 10, colour(255,255,255))
        
        # Atualiza o display
        self.lcd.show()
    
    def run(self):
        """Loop principal"""
        while True:
            try:
                # Escaneia redes
                networks = self.scan_networks()
                
                # Ordena por força do sinal (RSSI)
                networks.sort(key=lambda x: x[3], reverse=True)
                
                # Mostra no display
                self.draw_network_info(networks)
                
                # Aguarda antes do próximo scan
                time.sleep(5)
                
            except Exception as e:
                print(f"Erro: {e}")
                time.sleep(1)

def main():
    scanner = WiFiScanner()
    scanner.run()

if __name__ == "__main__":
    main() 