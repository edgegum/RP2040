import matplotlib.pyplot as plt
import numpy as np
from tkinter import Tk, filedialog

def escolher_arquivo():
    """Abre uma janela para escolher o arquivo .txt"""
    root = Tk()
    root.withdraw()  # Esconde a janela principal
    arquivo = filedialog.askopenfilename(
        title="Escolha o arquivo de dados",
        filetypes=[("Arquivos de texto", "*.txt")]
    )
    return arquivo

def ler_dados(arquivo):
    """Lê todos os dados do arquivo"""
    tempo_data = []
    valor_data = []
    
    try:
        with open(arquivo, 'r') as f:
            for linha in f:
                try:
                    timestamp, valor = linha.strip().split(',')
                    valor = int(valor)
                    tempo_data.append(len(tempo_data))
                    valor_data.append(valor)
                except Exception as e:
                    print(f"Erro ao processar linha: {linha.strip()} - {e}")
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        return None, None
    return tempo_data, valor_data

# Escolhe o arquivo
arquivo = escolher_arquivo()
if not arquivo:
    print("Nenhum arquivo selecionado!")
    exit(1)

# Lê os dados
tempo_data, valor_data = ler_dados(arquivo)
if not tempo_data or not valor_data:
    print("Erro ao ler dados!")
    exit(1)

# Cria o gráfico
plt.figure(figsize=(10, 6))
plt.plot(tempo_data, valor_data, 'g-')
plt.xlabel('Amostras')
plt.ylabel('Valor ADC')
plt.title(f'PWM Plotter - {len(valor_data)} pontos')
plt.grid(True)

# Mostra o gráfico
plt.show() 