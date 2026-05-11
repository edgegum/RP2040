from machine import UART, Pin, SPI, PWM
import time
import framebuf

# Configuração dos pinos UART para o GPS
GPS_RX = 5  # Pino RX do GPS (GPIO 5)
GPS_TX = 4  # Pino TX do GPS (GPIO 4)

# Comandos de inicialização para o VK2828U7G5LF
INIT_COMMANDS = [
    # Configura taxa de atualização para 1Hz
    b'$PMTK220,1000*1F\r\n',
    # Habilita GGA, RMC, GSA e GSV
    b'$PMTK314,0,1,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0*28\r\n',
    # Configura para modo de navegação normal
    b'$PMTK886,1*29\r\n',
    # Habilita saída de dados
    b'$PMTK301,2*2E\r\n'
]

# Pinos do display
BL = 13
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

class NMEABuffer:
    def __init__(self, size=1024):
        self.buffer = bytearray(size)
        self.head = 0
        self.tail = 0
        self.size = size

    def write(self, data):
        for byte in data:
            self.buffer[self.head] = byte
            self.head = (self.head + 1) % self.size

    def readline(self):
        line = []
        while self.tail != self.head:
            byte = self.buffer[self.tail]
            self.tail = (self.tail + 1) % self.size
            if byte == ord('\n'):
                return bytes(line)
            line.append(byte)
        return None

class GPS:
    def __init__(self):
        # Inicializa a comunicação UART com o GPS
        self.uart = UART(1, baudrate=9600, rx=Pin(GPS_RX), tx=Pin(GPS_TX))
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0
        self.speed = 0.0
        self.satellites = 0
        self.fix = False
        self.fix_quality = 0
        self.time = ""
        self.date = ""
        self.magnetic_declination = 0.0
        self.datum = "WGS84"
        
        # Informações adicionais do GSA
        self.fix_type = 0  # 0=No fix, 1=2D, 2=3D
        self.pdop = 0.0    # Position Dilution of Precision
        self.hdop = 0.0    # Horizontal Dilution of Precision
        self.vdop = 0.0    # Vertical Dilution of Precision
        
        # Informações do GSV
        self.visible_satellites = 0
        self.satellite_info = []
        
        # Buffer NMEA
        self.nmea_buffer = NMEABuffer()
        
        # Inicializa o GPS com os comandos de configuração
        self._initialize_gps()
    
    def _verify_checksum(self, line):
        """Verifica o checksum de uma mensagem NMEA"""
        try:
            if '*' not in line:
                return False
            message, checksum = line.split('*')
            calculated = 0
            for char in message[1:]:  # Ignora o $
                calculated ^= ord(char)
            return int(checksum, 16) == calculated
        except:
            return False
    
    def _initialize_gps(self):
        """Envia comandos de inicialização para o GPS"""
        print("Inicializando GPS...")
        
        # Envia comandos de configuração
        print("\nEnviando comandos de configuração...")
        for cmd in INIT_COMMANDS:
            print(f"Enviando comando: {cmd.decode('utf-8').strip()}")
            self.uart.write(cmd)
            time.sleep(0.5)
    
    def update(self):
        """Atualiza os dados do GPS lendo a porta serial"""
        if self.uart.any():
            try:
                # Lê dados disponíveis e adiciona ao buffer
                data = self.uart.read(self.uart.any())
                if data:
                    self.nmea_buffer.write(data)
                
                # Processa linhas completas do buffer
                while True:
                    line = self.nmea_buffer.readline()
                    if not line:
                        break
                    
                    try:
                        # Decodifica a linha de bytes para string
                        line = line.decode('utf-8').strip()
                        # Verifica o checksum
                        if self._verify_checksum(line):
                            # Mostra a linha NMEA bruta
                            print(f"NMEA: {line}")
                            # Processa a linha NMEA
                            self._parse_nmea(line)
                        else:
                            print(f"Erro de checksum na mensagem: {line}")
                    except UnicodeError:
                        print("Erro ao decodificar mensagem NMEA")
            except Exception as e:
                print(f"Erro ao ler GPS: {e}")
    
    def _parse_nmea(self, line):
        """Processa uma linha NMEA do GPS"""
        if line.startswith('$GPGGA'):  # Linha que contém dados de posição
            self._parse_gga(line)
        elif line.startswith('$GPRMC'):  # Linha que contém dados de velocidade e data
            self._parse_rmc(line)
        elif line.startswith('$GPGSA'):  # Linha que contém dados de precisão
            self._parse_gsa(line)
        elif line.startswith('$GPGSV'):  # Linha que contém dados dos satélites
            self._parse_gsv(line)
    
    def _parse_gga(self, line):
        """Processa mensagem GGA (Global Positioning System Fix Data)"""
        try:
            fields = line.split(',')
            if len(fields) >= 15:
                # Extrai a hora
                self.time = fields[1] if fields[1] else ""
                # Extrai latitude
                lat = fields[2]
                lat_dir = fields[3]
                # Extrai longitude
                lon = fields[4]
                lon_dir = fields[5]
                # Extrai qualidade do fix
                try:
                    self.fix_quality = int(fields[6]) if fields[6] else 0
                except ValueError:
                    self.fix_quality = 0
                # Extrai número de satélites
                try:
                    self.satellites = int(fields[7]) if fields[7] else 0
                except ValueError:
                    self.satellites = 0
                # Extrai altitude
                try:
                    self.altitude = float(fields[9]) if fields[9] else 0.0
                except ValueError:
                    self.altitude = 0.0
                
                # Converte latitude e longitude para formato decimal
                if lat and lon and lat_dir and lon_dir:
                    self.latitude = self._convert_coordinate(lat, lat_dir)
                    self.longitude = self._convert_coordinate(lon, lon_dir)
                    self.fix = self.fix_quality > 0
        except Exception as e:
            print(f"Erro ao processar GGA: {e}")
    
    def _parse_rmc(self, line):
        """Processa mensagem RMC (Recommended Minimum Navigation Information)"""
        try:
            fields = line.split(',')
            if len(fields) >= 13:
                # Verifica se o status é válido (A = válido, V = inválido)
                if fields[2] == 'A':  # Status válido
                    # Extrai a data
                    if len(fields[9]) == 6:
                        self.date = f"{fields[9][0:2]}/{fields[9][2:4]}/{fields[9][4:6]}"
                    # Extrai a velocidade em nós
                    try:
                        if fields[7]:
                            self.speed = float(fields[7]) * 1.852  # Converte nós para km/h
                    except ValueError:
                        self.speed = 0.0
        except Exception as e:
            print(f"Erro ao processar RMC: {e}")
    
    def _parse_gsa(self, line):
        """Processa mensagem GSA (GNSS DOP and Active Satellites)"""
        try:
            fields = line.split(',')
            if len(fields) >= 18:
                # Extrai o tipo de fix
                try:
                    self.fix_type = int(fields[2]) if fields[2] else 0
                except ValueError:
                    self.fix_type = 0
                
                # Extrai os valores de DOP
                try:
                    self.pdop = float(fields[15]) if fields[15] else 0.0
                    self.hdop = float(fields[16]) if fields[16] else 0.0
                    self.vdop = float(fields[17]) if fields[17] else 0.0
                except ValueError:
                    self.pdop = self.hdop = self.vdop = 0.0
        except Exception as e:
            print(f"Erro ao processar GSA: {e}")
    
    def _parse_gsv(self, line):
        """Processa mensagem GSV (GNSS Satellites in View)"""
        try:
            fields = line.split(',')
            if len(fields) >= 4:
                # Extrai o número total de satélites visíveis
                try:
                    self.visible_satellites = int(fields[3]) if fields[3] else 0
                except ValueError:
                    self.visible_satellites = 0
                
                # Processa informações dos satélites
                if len(fields) >= 8:
                    sat_info = {
                        'id': int(fields[4]) if fields[4] else 0,
                        'elevation': int(fields[5]) if fields[5] else 0,
                        'azimuth': int(fields[6]) if fields[6] else 0,
                        'snr': int(fields[7]) if fields[7] else 0
                    }
                    self.satellite_info.append(sat_info)
        except Exception as e:
            print(f"Erro ao processar GSV: {e}")
    
    def _convert_coordinate(self, coord, direction):
        """Converte coordenada do formato NMEA para decimal"""
        try:
            # Formato NMEA: DDMM.MMMM para latitude, DDDMM.MMMM para longitude
            if len(coord) >= 5:  # Garante que temos pelo menos DDMM
                # Encontra a posição do ponto decimal
                dot_pos = coord.find('.')
                if dot_pos == -1:
                    return 0.0
                
                # Para longitude (DDDMM.MMMM)
                if len(coord) > 5:
                    degrees = int(coord[:dot_pos-2])  # Tudo antes dos minutos
                    minutes = float(coord[dot_pos-2:])  # Os dois últimos dígitos antes do ponto + decimal
                # Para latitude (DDMM.MMMM)
                else:
                    degrees = int(coord[:dot_pos-2])  # Tudo antes dos minutos
                    minutes = float(coord[dot_pos-2:])  # Os dois últimos dígitos antes do ponto + decimal
                
                # Converte para decimal
                decimal = degrees + minutes / 60.0
                
                # Aplica o sinal baseado na direção
                if direction in ['S', 'W']:
                    decimal = -decimal
                
                return decimal
            return 0.0
        except Exception as e:
            print(f"Erro na conversão de coordenada: {e}")
            print(f"Valor recebido: {coord}, Direção: {direction}")
            return 0.0
    
    def has_fix(self):
        """Retorna True se o GPS tem fix"""
        return self.fix

# Primeiro testa o GPS sozinho
print("Testando GPS...")
gps = GPS()

try:
    # Testa o GPS por 10 segundos
    start_time = time.time()
    while time.time() - start_time < 10:
        gps.update()
        
        if gps.has_fix():
            print("\nGPS adquiriu fix!")
            print(f"Data/Hora: {gps.date} {gps.time}")
            print(f"Latitude: {gps.latitude:.6f}")
            print(f"Longitude: {gps.longitude:.6f}")
            print(f"Altitude: {gps.altitude:.1f}m")
            print(f"Velocidade: {gps.speed:.1f}km/h")
            print(f"Satélites: {gps.satellites}")
            break
        else:
            print(f"\rAguardando fix... Satélites: {gps.satellites}", end="")
        
        time.sleep(1)
    
    # Se chegou aqui, o GPS está funcionando
    print("\nGPS funcionando! Inicializando display...")
    
    # Agora inicializa o display
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

    def update_display(gps):
        """Atualiza o display com os dados do GPS"""
        lcd.fill(colour(0,0,0))  # Limpa o display
        
        # Título
        lcd.text("GPS Status", 10, 5, colour(255,255,0))
        
        # Fix e Satélites
        fix_color = colour(0,255,0) if gps.fix else colour(255,0,0)
        lcd.text(f"Fix: {'Sim' if gps.fix else 'Nao'}", 10, 20, fix_color)
        lcd.text(f"Satelites: {gps.satellites}", 10, 35, colour(255,255,255))
        
        # Data/Hora
        if gps.date and gps.time:
            lcd.text(f"{gps.date} {gps.time}", 10, 50, colour(255,255,255))
        
        # Coordenadas
        if gps.fix or (gps.latitude != 0.0 and gps.longitude != 0.0):  # Mostra valores se tiver fix ou se já tiver obtido coordenadas antes
            lcd.text(f"Lat: {gps.latitude:.6f}", 10, 65, colour(255,255,255))
            lcd.text(f"Lon: {gps.longitude:.6f}", 10, 80, colour(255,255,255))
            lcd.text(f"Alt: {gps.altitude:.1f}m", 10, 95, colour(255,255,255))
            lcd.text(f"Vel: {gps.speed:.1f}km/h", 10, 110, colour(255,255,255))
            # Mostra a declinação magnética e o datum
            lcd.text(f"Decl: {gps.magnetic_declination:.1f}°", 10, 125, colour(255,255,255))
            lcd.text(f"Datum: {gps.datum}", 10, 140, colour(255,255,255))
        else:
            lcd.text("Aguardando fix...", 10, 65, colour(255,0,0))
            lcd.text(f"Satelites: {gps.satellites}", 10, 80, colour(255,255,255))
        
        lcd.show()

    # Loop principal com display
    print("Iniciando loop principal com display...")
    last_fix_time = 0  # Variável para controlar o último fix válido
    while True:
        gps.update()
        
        # Atualiza o display
        update_display(gps)
        
        # Mostra também no console
        if gps.has_fix():
            last_fix_time = time.time()  # Atualiza o tempo do último fix
            print("\nDados do GPS:")
            print(f"Data/Hora: {gps.date} {gps.time}")
            print(f"Latitude: {gps.latitude:.6f}")
            print(f"Longitude: {gps.longitude:.6f}")
            print(f"Altitude: {gps.altitude:.1f}m")
            print(f"Velocidade: {gps.speed:.1f}km/h")
            print(f"Satélites: {gps.satellites}")
        else:
            # Só mostra a mensagem de "Aguardando fix..." se não tiver tido fix nos últimos 5 segundos
            if time.time() - last_fix_time > 5:
                print(f"\rAguardando fix... Satélites: {gps.satellites}", end="")
        
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\nPrograma finalizado")
except Exception as e:
    print(f"Erro: {e}")
finally:
    if 'lcd' in locals():
        lcd.fill(colour(0,0,0))  # Limpa o display ao finalizar
        lcd.show() 