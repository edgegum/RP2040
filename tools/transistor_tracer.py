import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import time

class TransistorTracer:
    def __init__(self):
        # Configurações iniciais
        self.vce_max = 10.0  # Tensão máxima coletor-emissor (V)
        self.ic_max = 0.1    # Corrente máxima de coletor (A)
        self.ib_steps = 5    # Número de passos de corrente de base
        self.points = 100    # Número de pontos por curva
        
        # Arrays para armazenar dados
        self.vce = np.linspace(0, self.vce_max, self.points)
        self.ib_values = np.linspace(0, self.ic_max/100, self.ib_steps)  # Ib = Ic/100 (aproximadamente)
        self.ic_curves = []
        
        # Configuração do gráfico
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        plt.subplots_adjust(bottom=0.25)  # Espaço para os controles
        
        # Inicializa as curvas
        self._init_curves()
        
        # Adiciona controles
        self._add_controls()
        
        # Configura o gráfico
        self._setup_plot()
        
    def _init_curves(self):
        """Inicializa as curvas de coletor"""
        self.ic_curves = []
        for ib in self.ib_values:
            # Modelo simplificado de transistor
            # Ic = beta * Ib * (1 - exp(-Vce/Vt))
            beta = 100  # Ganho de corrente
            vt = 0.026  # Tensão térmica (V)
            ic = beta * ib * (1 - np.exp(-self.vce/vt))
            self.ic_curves.append(ic)
    
    def _add_controls(self):
        """Adiciona controles interativos ao gráfico"""
        # Slider para beta
        ax_beta = plt.axes([0.25, 0.15, 0.65, 0.03])
        self.beta_slider = Slider(
            ax=ax_beta,
            label='Beta',
            valmin=50,
            valmax=200,
            valinit=100,
            valstep=1
        )
        
        # Slider para número de curvas
        ax_curves = plt.axes([0.25, 0.1, 0.65, 0.03])
        self.curves_slider = Slider(
            ax=ax_curves,
            label='Número de Curvas',
            valmin=2,
            valmax=10,
            valinit=5,
            valstep=1
        )
        
        # Botão de reset
        ax_reset = plt.axes([0.8, 0.025, 0.1, 0.04])
        self.reset_button = Button(ax_reset, 'Reset')
        
        # Conecta os eventos
        self.beta_slider.on_changed(self._update)
        self.curves_slider.on_changed(self._update)
        self.reset_button.on_clicked(self._reset)
    
    def _setup_plot(self):
        """Configura o gráfico"""
        self.ax.set_xlabel('Vce (V)')
        self.ax.set_ylabel('Ic (A)')
        self.ax.set_title('Curvas de Coletor do Transistor')
        self.ax.grid(True)
        
        # Plota as curvas iniciais
        self.lines = []
        for ic in self.ic_curves:
            line, = self.ax.plot(self.vce, ic, 'b-')
            self.lines.append(line)
        
        # Adiciona legenda
        self.ax.legend([f'Ib = {ib*1000:.1f}mA' for ib in self.ib_values])
    
    def _update(self, val):
        """Atualiza o gráfico quando os controles são alterados"""
        beta = self.beta_slider.val
        n_curves = int(self.curves_slider.val)
        
        # Atualiza valores de Ib
        self.ib_values = np.linspace(0, self.ic_max/100, n_curves)
        
        # Atualiza curvas
        for i, ib in enumerate(self.ib_values):
            vt = 0.026  # Tensão térmica (V)
            ic = beta * ib * (1 - np.exp(-self.vce/vt))
            self.ic_curves[i] = ic
            self.lines[i].set_ydata(ic)
        
        # Atualiza legenda
        self.ax.legend([f'Ib = {ib*1000:.1f}mA' for ib in self.ib_values])
        
        self.fig.canvas.draw_idle()
    
    def _reset(self, event):
        """Reseta os controles para os valores iniciais"""
        self.beta_slider.reset()
        self.curves_slider.reset()
    
    def show(self):
        """Mostra o gráfico"""
        plt.show()

def main():
    # Cria e mostra o traçador de transistor
    tracer = TransistorTracer()
    tracer.show()
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(8, 6))
ax.axis('off')

# Draw ground
ax.plot([1, 1.5], [1, 1], color='black')
ax.plot([1.25, 1.25], [0.8, 1], color='black')
ax.plot([1.15, 1.35], [0.8, 0.8], color='black')
ax.text(1.1, 0.7, 'GND', fontsize=10)

# Draw NPN transistor
ax.plot([2, 2], [1.5, 2.5], color='black', lw=2)  # Collector to emitter
ax.plot([2, 2.3], [2.5, 2.8], color='black', lw=2)  # Collector
ax.plot([2, 1.7], [1.5, 1.2], color='black', lw=2)  # Emitter
ax.add_patch(mpatches.FancyArrow(1.7, 1.2, 0.1, 0.1, width=0.03, head_width=0.1, head_length=0.1, color='black'))
ax.plot([2, 2.3], [2, 2], color='black', lw=2)  # Base
ax.text(2.35, 2.8, 'C', fontsize=12)
ax.text(2.35, 2, 'B', fontsize=12)
ax.text(2.35, 1.2, 'E', fontsize=12)
ax.text(2.05, 2.3, 'Q1\nNPN', fontsize=10)

# Draw R_shunt
ax.plot([2, 2], [1, 1.5], color='black', lw=2)
ax.add_patch(mpatches.Rectangle((1.9, 1), 0.2, 0.2, fill=False, edgecolor='black'))
ax.text(2.22, 1.05, 'R_shunt\n100Ω', fontsize=10)

# Draw PWM_base
ax.plot([0.5, 2], [2, 2], color='orange', lw=2)
ax.add_patch(mpatches.Rectangle((1.2, 1.9), 0.3, 0.2, fill=False, edgecolor='black'))
ax.text(1.1, 2.15, 'R_base\n4.7kΩ', fontsize=10)
ax.text(0.3, 2, 'PWM_base\n(GPIO2)', fontsize=10, color='orange')

# Draw PWM_coletor
ax.plot([2.3, 3.5], [2.8, 2.8], color='blue', lw=2)
ax.add_patch(mpatches.Rectangle((2.7, 2.7), 0.3, 0.2, fill=False, edgecolor='black'))
ax.text(3.1, 2.95, '10kΩ', fontsize=10)
ax.add_patch(mpatches.Rectangle((3.5, 2.7), 0.2, 0.2, fill=False, edgecolor='black'))
ax.text(3.75, 2.95, '10µF', fontsize=10)
ax.plot([3.7, 3.7], [2.8, 1], color='blue', lw=2)
ax.text(3.8, 2.8, 'PWM_coletor\n(GPIO3)', fontsize=10, color='blue')

# Draw ADC
ax.plot([2, 2.5], [1.1, 1.1], color='red', lw=2)
ax.text(2.55, 1.05, 'ADC\n(RP2040)', fontsize=10, color='red')

# Draw Vcc
ax.plot([3.7, 3.7], [2.8, 3.2], color='black')
ax.plot([3.5, 3.9], [3.2, 3.2], color='black')
ax.text(3.8, 3.25, '+3.3V', fontsize=10)

plt.title('Traçador de Curvas com PWM Base e Coletor (RP2040)', fontsize=14)
plt.savefig('tracador_curvas.png', bbox_inches='tight', dpi=200)
plt.show()

if __name__ == "__main__":
    main() 