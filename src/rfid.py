import machine
import time
import framebuf

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
        
        self.cs = machine.Pin(CS, machine.Pin.OUT)
        self.rst = machine.Pin(RST, machine.Pin.OUT)
        
        self.cs(1)
        self.spi = machine.SPI(1)
        self.spi = machine.SPI(1, 1000_000)
        self.spi = machine.SPI(1, 100000_000, polarity=0, phase=0, sck=machine.Pin(SCK), mosi=machine.Pin(MOSI), miso=None)
        self.dc = machine.Pin(DC, machine.Pin.OUT)
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

class RFID:
    def __init__(self):
        # Inicializa a UART para o protocolo Wiegand
        self.uart = machine.UART(1, baudrate=9600, tx=machine.Pin(4), rx=machine.Pin(5))
        self.uart.init(baudrate=9600, bits=8, parity=None, stop=1)
        
        # Buffer para armazenar dados recebidos
        self.buffer = bytearray()
        
        # Inicializa o display
        self.lcd = LCD_1inch14()
        self.lcd.fill(colour(0,0,0))
        self.lcd.show()
        
        # Configuração do brilho
        self.pwm = machine.PWM(machine.Pin(BL))
        self.pwm.freq(1000)
        self.pwm.duty_u16(32768)
        
        # Inicializa o RTC
        self.rtc = machine.RTC()
        
        # Configura a data e hora inicial (ajuste conforme necessário)
        # Formato: (ano, mês, dia, dia da semana, hora, minuto, segundo, microssegundo)
        self.rtc.datetime((2024, 3, 19, 2, 0, 0, 0, 0))
        
        # Controle de atualização do display
        self.last_display_update = 0
        self.display_update_interval = 2000  # Atualiza a cada 2 segundos
        self.last_card_id = None
        self.display_needs_update = True
        
    def get_timestamp(self):
        """Retorna a data e hora atual do RTC"""
        year, month, day, weekday, hour, minute, second, _ = self.rtc.datetime()
        return f"{day:02d}/{month:02d}/{year} {hour:02d}:{minute:02d}:{second:02d}"
        
    def set_datetime(self, year, month, day, hour, minute, second):
        """Configura a data e hora do RTC"""
        # Calcula o dia da semana (0 = Segunda, 6 = Domingo)
        # Usando a fórmula de Zeller
        if month < 3:
            month += 12
            year -= 1
        weekday = (day + (13 * (month + 1)) // 5 + year + year // 4 - year // 100 + year // 400) % 7
        # Ajusta para 0 = Segunda
        weekday = (weekday + 6) % 7
        
        self.rtc.datetime((year, month, day, weekday, hour, minute, second, 0))
        print(f"Data e hora configuradas: {self.get_timestamp()}")
        
    def read_card(self):
        """Lê um cartão RFID via protocolo Wiegand"""
        try:
            # Verifica se há dados disponíveis
            if self.uart.any():
                # Lê os dados disponíveis
                data = self.uart.read()
                if data:
                    # Processa os dados recebidos
                    # Formato Wiegand: 26 bits (8 bits de facility code + 16 bits de ID)
                    if len(data) >= 4:  # Mínimo de 4 bytes para um ID válido
                        # Extrai o ID do cartão (últimos 2 bytes)
                        card_id = (data[-2] << 8) | data[-1]
                        return f"{card_id:04X}"  # Retorna em formato hexadecimal
            return None
            
        except Exception as e:
            print(f"Erro ao ler cartão: {e}")
            return None
            
    def is_card_present(self):
        """Verifica se há um cartão presente"""
        try:
            return self.uart.any() > 0
        except:
            return False
            
    def update_display(self, card_id=None):
        """Atualiza o display com as informações do RFID e RTC"""
        current_time = time.ticks_ms()
        
        # Verifica se precisa atualizar o display
        if (time.ticks_diff(current_time, self.last_display_update) >= self.display_update_interval or 
            card_id != self.last_card_id or self.display_needs_update):
            
            self.lcd.fill(colour(0,0,0))  # Limpa o display
            
            # Título
            self.lcd.text("RFID Status", 10, 5, colour(255,255,0))
            
            # Data e hora
            timestamp = self.get_timestamp()
            self.lcd.text(timestamp, 10, 105, colour(255,255,255))
            
            if card_id:
                # Cartão detectado
                self.lcd.text("Cartao Detectado:", 10, 25, colour(0,255,0))
                self.lcd.text(card_id, 10, 45, colour(255,255,255))
                self.lcd.text("Status: Autorizado", 10, 65, colour(0,255,0))
            else:
                # Aguardando cartão
                self.lcd.text("Aguardando cartao...", 10, 25, colour(255,255,255))
                self.lcd.text("Aproxime um cartao", 10, 45, colour(255,255,255))
                self.lcd.text("Status: Aguardando", 10, 65, colour(255,255,255))
            
            self.lcd.show()
            self.last_display_update = current_time
            self.last_card_id = card_id
            self.display_needs_update = False

# Exemplo de uso
if __name__ == "__main__":
    print("Iniciando leitor RFID Wiegand...")
    rfid = RFID()
    
    print("\nComandos disponíveis:")
    print("  rfid.set_datetime(2024, 3, 19, 14, 30, 0) - Configura data e hora")
    print("  rfid.get_timestamp() - Mostra a data e hora atual")
    print("  rfid.update_display() - Atualiza o display")
    
    try:
        while True:
            # Prioriza a leitura do RFID
            if rfid.is_card_present():
                card_id = rfid.read_card()
                if card_id:
                    print(f"Cartão detectado: {card_id}")
                    rfid.update_display(card_id)
                time.sleep(0.5)  # Reduzido para 0.5 segundos
            else:
                # Atualiza o display apenas se necessário
                rfid.update_display()
            
            # Pequena pausa para não sobrecarregar
            time.sleep(0.05)  # Reduzido para 0.05 segundos
            
    except KeyboardInterrupt:
        print("\nPrograma finalizado")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        rfid.lcd.fill(colour(0,0,0))  # Limpa o display ao finalizar
        rfid.lcd.show() 