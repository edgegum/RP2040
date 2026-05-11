from machine import Pin, SPI, PWM, ADC, UART
import framebuf
import utime
from rp2 import PIO, asm_pio

# Pinos do display
BL = 13
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

# Programa para o PIO do DHT
@asm_pio(set_init=(PIO.OUT_HIGH),autopush=True, push_thresh=8) 
def DHT_PIO():
    pull()
    set(pindirs,1)              
    set(pins,0)                 
    mov (x,osr)
    label ('waitx')
    nop() [25] 
    jmp(x_dec,'waitx')          
    set(pindirs,0)              
    wait(1,pin,0)               
    wait(0,pin,0)               
    wait(1,pin,0)
    wait(0,pin,0)               
    label('readdata')
    wait(1,pin,0)               
    set(x,20)                   
    label('countdown')
    jmp(pin,'continue')         
    set(y,0)                 
    in_(y, 1)                   
    jmp('readdata')             
    label('continue')
    jmp(x_dec,'countdown')      
    set(y,1)                  
    in_(y, 1)                   
    wait(0,pin,0)               
    jmp('readdata')             

# Constantes do DHT
DHT11 = 0
DHT22 = 1

# Classe do DHT
class DHT:
    def __init__(self, dataPin, modelo, smID=0):
        self.dataPin = dataPin
        self.modelo = modelo
        self.smID = smID
        self.sm = rp2.StateMachine(self.smID)
        self.ultleitura = 0
        self.data=[]
     
    def leitura(self):
        data=[]
        self.sm.init(DHT_PIO,freq=1400000,set_base=self.dataPin,in_base=self.dataPin,jmp_pin=self.dataPin)
        self.sm.active(1)
        if self.modelo == DHT11:
            self.sm.put(969)     # espera 18 milisegundos
        else:
            self.sm.put(54)      # espera 1 milisegundo
        for i in range(5):       # lê os 5 bytes da resposta
            data.append(self.sm.get())
        self.sm.active(0)
        total=0
        for i in range(4):
            total=total+data[i]
        if data[4] == (total & 0xFF):
            self.data = data
            self.ultleitura = utime.ticks_ms()
            return True
        else:
            return False
 
    def obtemDados(self):
        while len(self.data) == 0:
            if not self.leitura():
                utime.sleep_ms(2000)
        agora = utime.ticks_ms()
        if self.ultleitura > agora:
            self.ultleitura = agora
        if (self.ultleitura+2000) < agora:
            self.leitura()
     
    def umidade(self):
        self.obtemDados()
        if self.modelo == DHT11:
            return self.data[0] + self.data[1]*0.1
        else:
            return ((self.data[0] << 8) + self.data[1]) * 0.1
 
    def temperatura(self):
        self.obtemDados()
        if self.modelo == DHT11:
            return self.data[2] + self.data[3]*0.1
        else:
            s = 1
            if (self.data[2] & 0x80) == 1:
                s = -1
            return s * (((self.data[2] & 0x7F) << 8) + self.data[3]) * 0.1

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

# Inicialização do Bluetooth
bluetooth = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# Configuração do DHT11
dht_data = Pin(28, Pin.IN, Pin.PULL_UP)
dht = DHT(dht_data, DHT11, 0)

# Função para obter temperatura interna
def temperatura_interna():
    sensor_temp = ADC(4)
    fator_conversao = 3.3 / (65535)
    leitura = sensor_temp.read_u16() * fator_conversao
    temperatura = 27 - (leitura - 0.706)/0.001721
    return temperatura

print("Iniciando monitoramento...")

while True:
    try:
        # Limpa a tela
        lcd.fill(colour(0,0,0))
        
        # Tenta ler o DHT11
        if dht.leitura():
            temp = dht.temperatura()
            umid = dht.umidade()
            print(f"DHT11 - Temp: {temp:.1f}C, Umid: {umid:.1f}%")
            
            # Envia via Bluetooth
            bluetooth.write(f"TEMP:{temp:.1f},UMID:{umid:.1f}\r\n".encode())
            
            # Mostra no display
            lcd.text("DHT11 Conectado", 5, 5, colour(0,255,0))
            lcd.text(f"Temp: {temp:.1f}C", 5, 25, colour(0,255,0))
            lcd.text(f"Umid: {umid:.1f}%", 5, 45, colour(0,255,0))
        else:
            temp = temperatura_interna()
            print(f"DHT11 nao encontrado - Temp Interna: {temp:.1f}C")
            
            # Envia via Bluetooth
            bluetooth.write(f"TEMP:{temp:.1f},UMID:N/A\r\n".encode())
            
            # Mostra no display
            lcd.text("DHT11 Nao Encontrado", 5, 5, colour(255,0,0))
            lcd.text(f"Temp Interna: {temp:.1f}C", 5, 25, colour(255,0,0))
        
        # Atualiza display
        lcd.show()
        
        # Aguarda 2 segundos
        utime.sleep_ms(2000)
        
    except Exception as e:
        print(f"Erro: {e}")
        lcd.fill(colour(0,0,0))
        lcd.text("Erro:", 5, 5, colour(255,0,0))
        lcd.text(str(e), 5, 25, colour(255,0,0))
        lcd.show()
        utime.sleep_ms(2000) 