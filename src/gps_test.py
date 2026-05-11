from machine import UART, Pin
import time

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
    b'$PMTK301,2*2E\r\n'
]

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
        
        # Inicializa o GPS com os comandos de configuração
        self._initialize_gps()
        
    def _initialize_gps(self):
        """Envia comandos de inicialização para o GPS"""
        print("Inicializando GPS...")
        
        # Depois envia comandos de configuração
        print("\nEnviando comandos de configuração...")
        for cmd in INIT_COMMANDS:
            print(f"Enviando comando: {cmd.decode('utf-8').strip()}")
            self.uart.write(cmd)
            time.sleep(0.5)
    
    def update(self):
        """Atualiza os dados do GPS lendo a porta serial"""
        if self.uart.any():
            try:
                # Lê uma linha completa do GPS
                line = self.uart.readline()
                if line:
                    # Decodifica a linha de bytes para string
                    line = line.decode('utf-8').strip()
                    # Mostra a linha NMEA bruta
                    print(f"NMEA: {line}")
                    # Processa a linha NMEA
                    self._parse_nmea(line)
            except Exception as e:
                print(f"Erro ao ler GPS: {e}")
    
    def _parse_nmea(self, line):
        """Processa uma linha NMEA do GPS"""
        if line.startswith('$GPGGA'):  # Linha que contém dados de posição
            try:
                # Divide a linha em campos
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
                print(f"Erro ao processar dados NMEA: {e}")
        elif line.startswith('$GPRMC'):  # Linha que contém dados de velocidade e data
            try:
                fields = line.split(',')
                if len(fields) >= 13:
                    # Extrai a data
                    self.date = fields[9] if fields[9] else ""
                    # Extrai a velocidade em nós
                    if fields[7]:
                        try:
                            self.speed = float(fields[7]) * 1.852  # Converte nós para km/h
                        except ValueError:
                            self.speed = 0.0
            except Exception as e:
                print(f"Erro ao processar dados RMC: {e}")
    
    def _convert_coordinate(self, coord, direction):
        """Converte coordenada do formato NMEA para decimal"""
        try:
            # Formato NMEA: DDMM.MMMM
            degrees = float(coord[:2])
            minutes = float(coord[2:])
            decimal = degrees + minutes / 60.0
            if direction in ['S', 'W']:
                decimal = -decimal
            return decimal
        except:
            return 0.0
    
    def get_position(self):
        """Retorna a posição atual (latitude, longitude)"""
        return (self.latitude, self.longitude)
    
    def get_altitude(self):
        """Retorna a altitude atual"""
        return self.altitude
    
    def get_speed(self):
        """Retorna a velocidade atual em km/h"""
        return self.speed
    
    def get_satellites(self):
        """Retorna o número de satélites visíveis"""
        return self.satellites
    
    def get_time(self):
        """Retorna a hora atual do GPS"""
        return self.time
    
    def get_date(self):
        """Retorna a data atual do GPS"""
        return self.date
    
    def has_fix(self):
        """Retorna True se o GPS tem fix"""
        return self.fix

# Exemplo de uso
if __name__ == "__main__":
    print("Iniciando GPS...")
    gps = GPS()
    
    try:
        while True:
            gps.update()
            
            if gps.has_fix():
                print("\nDados do GPS:")
                print(f"Latitude: {gps.latitude:.6f}")
                print(f"Longitude: {gps.longitude:.6f}")
                print(f"Altitude: {gps.altitude:.1f}m")
                print(f"Velocidade: {gps.speed:.1f}km/h")
                print(f"Satélites: {gps.satellites}")
                print(f"Data/Hora: {gps.date} {gps.time}")
            else:
                print(f"\rAguardando fix... Satélites: {gps.satellites}", end="")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nPrograma finalizado")
    except Exception as e:
        print(f"Erro: {e}") 