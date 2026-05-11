from machine import Pin,I2C
from rp2 import PIO
from time import sleep
from random import randrange
import framebuf
import ssd1306

# Endereços I2C comuns para displays OLED
OLED_ADDRESSES = [0x3C, 0x3D]

try:
    # Configura os pinos I2C com pull-up interno
    scl = Pin(5, Pin.OUT, Pin.PULL_UP)
    sda = Pin(4, Pin.OUT, Pin.PULL_UP)
    
    # Inicializa I2C com os pinos configurados
    i2c = I2C(0, scl=scl, sda=sda)
    
    # Verifica dispositivos I2C conectados
    print("Procurando dispositivos I2C...")
    devices = i2c.scan()
    if len(devices) == 0:
        print("Nenhum dispositivo I2C encontrado!")
        print("Verifique as conexões:")
        print("- SDA conectado ao pino 4")
        print("- SCL conectado ao pino 5")
        print("- VCC conectado a 3.3V")
        print("- GND conectado ao GND")
        raise Exception("Nenhum dispositivo I2C encontrado")
    
    print("Dispositivos I2C encontrados nos endereços:", [hex(d) for d in devices])
    
    # Tenta inicializar o display com diferentes endereços
    display = None
    for addr in OLED_ADDRESSES:
        try:
            print(f"Tentando inicializar display no endereço 0x{addr:02X}...")
            display = ssd1306.SSD1306_I2C(128, 64, i2c, addr=addr)
            print(f"Display inicializado com sucesso no endereço 0x{addr:02X}!")
            break
        except Exception as e:
            print(f"Falha ao inicializar no endereço 0x{addr:02X}: {str(e)}")
            continue
    
    if display is None:
        raise Exception("Não foi possível inicializar o display em nenhum endereço")
    
    # Testa o display
    display.fill(0)
    display.text("Teste OLED", 0, 0)
    display.show()
    print("Teste de escrita realizado com sucesso!")

except Exception as e:
    print("\nErro:", str(e))
    print("Tipo do erro:", type(e).__name__)
    print("\nSugestões de solução:")
    print("1. Verifique todas as conexões físicas")
    print("2. Confirme se o display está recebendo alimentação")
    print("3. Se ainda não funcionar, tente usar resistores pull-up externos de 4.7kΩ")
    print("4. Verifique se o display não está danificado")
    raise

# Carrega imagem
def loadPBM(arq, tamX, tamY):
    with open(arq, 'rb') as f:
        f.readline() # Magic number
        f.readline() # Creator comment
        f.readline() # Dimensions
        data = bytearray(f.read())
    return framebuf.FrameBuffer(data, tamX, tamY, framebuf.MONO_HLSB)
 
#fbuf = loadPBM('MakerHero.pbm', 128, 39)
 
# Mostra a imagem no display
#display.blit(fbuf, 0, 16)
#display.show()
#sleep(5)
 
# Limpa a imagem
display.fill_rect(0, 16, 128, 48, 0)
 
# Vamos fazer um gráfico de barras aleatórias
while True:
    for x in range(0, 128, 16):
        y = randrange (10, 50)
        display.fill_rect(x, 10, 12, 54, 0)
        display.fill_rect(x, y, 12, 64-y, 1)
    display.show()
    sleep(1)