import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# CONFIGURAÇÕES
PORTA = 'COM8'  # Altere para a porta correta do seu RP2040
BAUD = 115200
TIMEOUT = 1

# Inicializa serial
ser = serial.Serial(PORTA, BAUD, timeout=TIMEOUT)

# Dados para plotar
vce_data = []
ic_data = []
curva_atual = []

fig, ax = plt.subplots()
line, = ax.plot([], [], 'b.-')
ax.set_xlabel('Vce (V)')
ax.set_ylabel('Ic (A)')
ax.set_title('Curva de Transistor - Dados Reais')
ax.grid(True)

def init():
    ax.set_xlim(0, 5)  # Ajuste conforme seu range de Vce
    ax.set_ylim(0, 0.1)  # Ajuste conforme seu range de Ic
    line.set_data([], [])
    return line,

def update(frame):
    global vce_data, ic_data, curva_atual
    while ser.in_waiting:
        try:
            linha = ser.readline().decode().strip()
            if not linha:
                continue
            # Espera que o RP2040 envie: Vce,Ic
            partes = linha.split(',')
            if len(partes) < 2:
                continue
            vce, ic = map(float, partes[:2])
            curva_atual.append((vce, ic))
            # Se detectar fim de curva (ex: Vce == 0 e len(curva_atual) > 1), inicia nova curva
            if vce == 0 and len(curva_atual) > 1:
                vce_data.append([p[0] for p in curva_atual])
                ic_data.append([p[1] for p in curva_atual])
                curva_atual = []
        except Exception as e:
            print("Erro ao processar linha:", linha, e)
    # Atualiza o gráfico com todas as curvas recebidas
    ax.clear()
    ax.set_xlabel('Vce (V)')
    ax.set_ylabel('Ic (A)')
    ax.set_title('Curva de Transistor - Dados Reais')
    ax.grid(True)
    for v, i in zip(vce_data, ic_data):
        ax.plot(v, i, '.-')
    if curva_atual:
        v, i = zip(*curva_atual)
        ax.plot(v, i, 'r.-')
    return line,

ani = animation.FuncAnimation(fig, update, init_func=init, blit=False, interval=100)
plt.show()
ser.close() 