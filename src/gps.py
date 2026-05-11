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
    # Habilita apenas GGA e RMC
    b'$PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28\r\n',
    # Configura para modo de navegação normal
    b'$PMTK886,1*29\r\n',
    # Habilita saída de dados
    b'$PMTK301,2*2E\r\n',
    # Configura para usar todos os satélites disponíveis
    b'$PMTK313,1*2E\r\n',
    # Configura para modo de navegação 2D/3D
    b'$PMTK386,0*23\r\n',
    # Configura para usar GPS + GLONASS
    b'$PMTK353,1,1,0,0,0*2A\r\n',
    # Configura para usar GPS + BEIDOU
    b'$PMTK353,1,0,0,1,0*2A\r\n',
    # Configura para usar GPS + GALILEO
    b'$PMTK353,1,0,0,0,1*2A\r\n'
]

# Comandos de teste para o GPS
TEST_COMMANDS = [
    # Solicita informações do firmware
    b'$PMTK605*31\r\n',
    # Solicita informações de hardware
    b'$PMTK400*36\r\n',
    # Solicita status do GPS
    b'$PMTK414*33\r\n'
]

# Pinos do display
BL = 13
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

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
        self.magnetic_declination = 0.0  # Declinação magnética em graus
        self.datum = "WGS84"  # Datum padrão do GPS
        # Buffer para controlar perdas de fix
        self.fix_buffer = [False] * 5  # Buffer de 5 leituras
        self.fix_buffer_index = 0
        self._initialize_gps()
    
    def _initialize_gps(self):
        """Envia comandos de inicialização para o GPS"""
        print("Inicializando GPS...")
        time.sleep(5)  # Aumenta o tempo de espera inicial para 5 segundos
        
        # Primeiro envia comandos de teste
        print("\nEnviando comandos de teste...")
        for cmd in TEST_COMMANDS:
            try:
                print(f"Enviando comando: {cmd.decode('utf-8').strip()}")
                self.uart.write(cmd)
                time.sleep(0.5)
                
                # Tenta ler a resposta
                if self.uart.any():
                    response = self.uart.readline()
                    if response:
                        try:
                            print(f"Resposta: {response.decode('utf-8').strip()}")
                        except UnicodeError:
                            print("Resposta recebida (não decodificável)")
            except Exception as e:
                print(f"Erro ao enviar comando: {e}")
        
        # Depois envia comandos de configuração
        print("\nEnviando comandos de configuração...")
        for cmd in INIT_COMMANDS:
            try:
                print(f"Enviando comando: {cmd.decode('utf-8').strip()}")
                self.uart.write(cmd)
                time.sleep(0.5)
                
                # Tenta ler a resposta
                if self.uart.any():
                    response = self.uart.readline()
                    if response:
                        try:
                            print(f"Resposta: {response.decode('utf-8').strip()}")
                        except UnicodeError:
                            print("Resposta recebida (não decodificável)")
            except Exception as e:
                print(f"Erro ao enviar comando: {e}")
        
        # Aguarda mais um pouco para o GPS processar as configurações
        print("\nAguardando GPS processar configurações...")
        time.sleep(5)
        
        # Limpa o buffer da UART
        while self.uart.any():
            self.uart.readline()
        
        print("Inicialização do GPS concluída")
    
    def update(self):
        """Atualiza os dados do GPS lendo a porta serial"""
        if self.uart.any():
            try:
                # Lê uma linha completa do GPS
                line = self.uart.readline()
                if line:
                    try:
                        # Decodifica a linha de bytes para string
                        line = line.decode('utf-8').strip()
                        # Verifica se a linha está completa (começa com $ e termina com *)
                        if line.startswith('$') and '*' in line:
                            # Mostra a linha NMEA bruta
                            print(f"NMEA: {line}")
                            # Processa a linha NMEA
                            self._parse_nmea(line)
                        else:
                            print(f"Linha NMEA incompleta: {line}")
                    except UnicodeError:
                        print("Erro ao decodificar mensagem NMEA")
            except Exception as e:
                print(f"Erro ao ler GPS: {e}")
    
    def _calculate_magnetic_declination(self, lat, lon):
        """Calcula a declinação magnética aproximada para as coordenadas fornecidas"""
        # Para Manaus e região, a declinação magnética é aproximadamente -12.5 graus
        # Fonte: https://www.ngdc.noaa.gov/geomag/calculators/magcalc.shtml
        return -12.5
    
    def _apply_magnetic_declination(self, lat, lon):
        """Aplica a correção da declinação magnética nas coordenadas"""
        # Calcula a declinação magnética
        self.magnetic_declination = self._calculate_magnetic_declination(lat, lon)
        
        # Aplica a correção
        # A declinação magnética é o ângulo entre o norte verdadeiro e o norte magnético
        # Para Manaus, a correção é aproximadamente 0.25 graus na longitude
        # A correção é mais significativa em latitudes mais altas
        import math
        
        # Converte para radianos
        lat_rad = math.radians(lat)
        
        # Calcula a correção em graus
        # A correção é proporcional à declinação e inversamente proporcional ao cosseno da latitude
        correction = self.magnetic_declination / (60.0 * math.cos(lat_rad))
        
        # Aplica a correção na longitude
        lon_corrected = lon + correction
        
        return lat, lon_corrected
    
    def _convert_datum(self, lat, lon, from_datum="WGS84", to_datum="SAD69"):
        """Converte coordenadas entre diferentes datums"""
        # Constantes para conversão WGS84 para SAD69
        # Fonte: IBGE
        if from_datum == "WGS84" and to_datum == "SAD69":
            # Correções para SAD69 (em graus)
            # Para Manaus e região
            lat_correction = 0.000002
            lon_correction = 0.000003
            
            # Aplica as correções
            lat_sad69 = lat + lat_correction
            lon_sad69 = lon + lon_correction
            
            return lat_sad69, lon_sad69
        return lat, lon  # Retorna as coordenadas originais se não houver conversão
    
    def _convert_coordinate(self, coord, direction):
        """Converte coordenada do formato NMEA para decimal"""
        try:
            # Formato NMEA: DDDMM.MMMM para longitude, DDMM.MMMM para latitude
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
    
    def _update_fix_buffer(self, has_fix):
        """Atualiza o buffer de fix e retorna True se a maioria das leituras recentes tem fix"""
        self.fix_buffer[self.fix_buffer_index] = has_fix
        self.fix_buffer_index = (self.fix_buffer_index + 1) % len(self.fix_buffer)
        # Retorna True se pelo menos 3 das últimas 5 leituras tiveram fix
        return sum(self.fix_buffer) >= 3

    def _parse_nmea(self, line):
        """Processa uma linha NMEA do GPS"""
        try:
            # Verifica se a linha está completa e válida
            if not line.startswith('$') or '*' not in line:
                return
                
            # Remove caracteres de controle
            line = line.strip()
            
            if line.startswith('$GPGGA'):  # Linha que contém dados de posição
                try:
                    # Divide a linha em campos
                    fields = line.split(',')
                    if len(fields) >= 15:
                        # Extrai a hora
                        if len(fields[1]) >= 6:
                            self.time = f"{fields[1][0:2]}:{fields[1][2:4]}:{fields[1][4:6]}"
                        
                        # Extrai latitude e longitude
                        lat = fields[2]
                        lat_dir = fields[3]
                        lon = fields[4]
                        lon_dir = fields[5]
                        
                        # Mostra os valores brutos para debug
                        print(f"\nValores brutos do GPS:")
                        print(f"Latitude: {lat} {lat_dir}")
                        print(f"Longitude: {lon} {lon_dir}")
                        
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
                            if fields[9]:
                                self.altitude = float(fields[9])
                                # Ajusta altitude negativa
                                if self.altitude < 0:
                                    self.altitude = 0.0
                        except ValueError:
                            self.altitude = 0.0
                        
                        # Verifica se tem fix válido nesta leitura
                        current_fix = self.fix_quality > 0 and lat and lon and lat_dir and lon_dir
                        
                        # Atualiza o buffer de fix
                        self.fix = self._update_fix_buffer(current_fix)
                        
                        # Só processa coordenadas se tiver fix válido
                        if self.fix:
                            # Converte latitude e longitude para formato decimal
                            self.latitude = self._convert_coordinate(lat, lat_dir)
                            self.longitude = self._convert_coordinate(lon, lon_dir)
                            
                            # Mostra os valores convertidos
                            print(f"\nValores convertidos:")
                            print(f"Latitude: {self.latitude:.6f}")
                            print(f"Longitude: {self.longitude:.6f}")
                        else:
                            print(f"Sem fix válido. Qualidade: {self.fix_quality}, Satélites: {self.satellites}")
                            print(f"Buffer de fix: {self.fix_buffer}")
                except Exception as e:
                    print(f"Erro ao processar GGA: {e}")
                    
            elif line.startswith('$GPRMC'):  # Linha que contém dados de velocidade e data
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
                        else:
                            print("Status RMC inválido")
                except Exception as e:
                    print(f"Erro ao processar RMC: {e}")
        except Exception as e:
            print(f"Erro ao processar NMEA: {e}")
    
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