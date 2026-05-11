import utime
import rp2 
from rp2 import PIO, asm_pio
from machine import Pin
import matplotlib.pyplot as plt
from collections import deque
import time

# Programa para o PIO
# coloca automaticamente na fila a cada 8 bits recebidos
@asm_pio(set_init=(PIO.OUT_HIGH),autopush=True, push_thresh=8) 
def DHT_PIO():
    # aguarda uma solicitação do programa
    pull()
     
    # mantem dado em 0 pelo tempo informado pelo programa
    set(pindirs,1)              #set pin to output  
    set(pins,0)                 #set pin low
    mov (x,osr)
    label ('waitx')
    nop() [25] 
    jmp(x_dec,'waitx')          # espera tempo*26/clock=x
      
    # inicia leitura da resposta
    set(pindirs,0)              # muda o pino para entrada
    wait(1,pin,0)               # aguarda voltar ao nível alto
    wait(0,pin,0)               # aguarda pulso inicial
    wait(1,pin,0)
    wait(0,pin,0)               # aguarda inicio do primeiro bit
 
    # lê os bits
    label('readdata')
    wait(1,pin,0)               # espera o sinal ir para nivel alto
    set(x,20)                   # registrador x é o timeout para descer
    label('countdown')
    jmp(pin,'continue')         # continua contando se sinal permanece alto
     
    # pino foi para o nível baixo antes da contagem terminar -> bit 0
    set(y,0)                 
    in_(y, 1)                   # coloca um 'zero' no resultado
    jmp('readdata')             # ler o próximo bit
     
    # pino continua no nível alto
    label('continue')
    jmp(x_dec,'countdown')      # decrementar a contagem
 
    # contagem terminou -> bit 1
    set(y,1)                  
    in_(y, 1)                   # coloca um 'um' no resultado
    wait(0,pin,0)               # espera voltar ao nível baixo
    jmp('readdata')             # ler o próximo bit
 
DHT11 = 0
DHT22 = 1
 
class DHT:
 
    # Construtor
    # dataPin: pino de dados
    # modelo:  DHT11 ou DHT22
    # smID:    identificador da máquina de estados
    def __init__(self, dataPin, modelo, smID=0):
        self.dataPin = dataPin
        self.modelo = modelo
        self.smID = smID
        self.sm = rp2.StateMachine(self.smID)
        self.ultleitura = 0
        self.data=[]
     
    # faz uma leitura no sensor
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
            # checksum ok, salvar os dados
            self.data = data
            self.ultleitura = utime.ticks_ms()
            return True
        else:
            return False
 
    # le ou usa dados já existentes
    def obtemDados(self):
        # garante ter dados
        while len(self.data) == 0:
            if not self.leitura():
                utime.sleep_ms(2000)
             
        # só tenta ler se já passou pelo menos 2 segundos da última leitura
        agora = utime.ticks_ms()
        if self.ultleitura > agora:
            self.ultleitura = agora  # contador deu a volta
        if (self.ultleitura+2000) < agora:
            self.leitura()
     
    # informa a umidade
    def umidade(self):
        self.obtemDados()
        if self.modelo == DHT11:
            return self.data[0] + self.data[1]*0.1
        else:
            return ((self.data[0] << 8) + self.data[1]) * 0.1
 
    # informa a temperatura
    def temperatura(self):
        self.obtemDados()
        if self.modelo == DHT11:
            return self.data[2] + self.data[3]*0.1
        else:
            s = 1
            if (self.data[2] & 0x80) == 1:
                s = -1
            return s * (((self.data[2] & 0x7F) << 8) + self.data[3]) * 0.1
 
#main program
dht_data = Pin(28, Pin.IN, Pin.PULL_UP)
dht = DHT(dht_data, DHT11, 0)  # Torque por DHT22 se usar este modelo

# Criar listas para armazenar dados
temperaturas = deque(maxlen=100)  # Armazena as últimas 100 leituras
tempos = deque(maxlen=100)        # Armazena os tempos correspondentes
inicio = time.time()

# Configurar o gráfico
plt.ion()  # Modo interativo
fig, ax = plt.subplots()
line, = ax.plot([], [])
ax.set_xlabel('Tempo (s)')
ax.set_ylabel('Temperatura (°C)')
ax.set_title('Variação de Temperatura')
ax.grid(True)

while True:
    temp = dht.temperatura()
    tempo_atual = time.time() - inicio
    
    # Adicionar novos dados
    temperaturas.append(temp)
    tempos.append(tempo_atual)
    
    # Atualizar o gráfico
    line.set_data(list(tempos), list(temperaturas))
    ax.relim()
    ax.autoscale_view()
    fig.canvas.draw()
    fig.canvas.flush_events()
    
    print("Umidade: %.1f%%, Temperatura: %.1fC" % 
          (dht.umidade(), temp))
    utime.sleep_ms(3000)