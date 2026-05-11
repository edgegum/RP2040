"""
Teste dos GPIOs Disponíveis no RP2040
=====================================

Este script testa todos os GPIOs disponíveis no seu RP2040:
- GPIO 29, 28, 5, 4, 3, 2

Pode ser usado para verificar se os pinos estão funcionando
antes de conectar os displays.

Autor: Baseado na estrutura dos scripts de display
"""

from machine import Pin
import time

# Configuração dos pinos disponíveis
GPIO_29 = Pin(29, Pin.OUT)  # Reset do Nokia 5110
GPIO_28 = Pin(28, Pin.OUT)  # Chip Enable do Nokia 5110
GPIO_5  = Pin(5,  Pin.OUT)  # Data/Command do Nokia 5110 ou CS do MAX7219
GPIO_4  = Pin(4,  Pin.OUT)  # Data In (DIN) - usado em ambos os displays
GPIO_3  = Pin(3,  Pin.OUT)  # Clock (CLK) - usado em ambos os displays
GPIO_2  = Pin(2,  Pin.OUT)  # LED de status ou botão

def test_gpio_sequence():
    """Testa uma sequência de piscamento em todos os GPIOs"""
    print("Iniciando teste dos GPIOs...")
    
    # Lista de todos os GPIOs disponíveis
    gpios = [GPIO_29, GPIO_28, GPIO_5, GPIO_4, GPIO_3, GPIO_2]
    gpio_names = ["GPIO_29", "GPIO_28", "GPIO_5", "GPIO_4", "GPIO_3", "GPIO_2"]
    
    # 1. Teste individual - cada GPIO pisca uma vez
    print("1. Teste individual de cada GPIO")
    for i, gpio in enumerate(gpios):
        print(f"   Testando {gpio_names[i]}...")
        gpio.on()
        time.sleep(0.5)
        gpio.off()
        time.sleep(0.2)
    
    # 2. Teste sequencial - todos piscam em sequência
    print("2. Teste sequencial")
    for _ in range(3):
        for gpio in gpios:
            gpio.on()
            time.sleep(0.1)
            gpio.off()
        time.sleep(0.3)
    
    # 3. Teste de onda - efeito de onda
    print("3. Teste de onda")
    for _ in range(2):
        # Onda da esquerda para direita
        for gpio in gpios:
            gpio.on()
            time.sleep(0.1)
        for gpio in gpios:
            gpio.off()
            time.sleep(0.1)
        
        time.sleep(0.5)
        
        # Onda da direita para esquerda
        for gpio in reversed(gpios):
            gpio.on()
            time.sleep(0.1)
        for gpio in reversed(gpios):
            gpio.off()
            time.sleep(0.1)
        
        time.sleep(0.5)
    
    # 4. Teste final - todos acesos e depois apagados
    print("4. Teste final - todos acesos")
    for gpio in gpios:
        gpio.on()
    time.sleep(1)
    
    for gpio in gpios:
        gpio.off()
    
    print("Teste dos GPIOs concluído!")

def test_display_pins():
    """Testa especificamente os pinos usados pelos displays"""
    print("\nTestando pinos específicos dos displays...")
    
    # Pinos do Nokia 5110
    print("Pinos do Nokia 5110:")
    nokia_pins = {
        "RST": GPIO_29,
        "CE":  GPIO_28,
        "DC":  GPIO_5,
        "DIN": GPIO_4,
        "CLK": GPIO_3
    }
    
    for name, pin in nokia_pins.items():
        print(f"   Testando {name} (GPIO {pin.pin()})...")
        pin.on()
        time.sleep(0.2)
        pin.off()
        time.sleep(0.1)
    
    # Pinos da Matriz LED 8x8
    print("Pinos da Matriz LED 8x8:")
    matrix_pins = {
        "DIN": GPIO_4,
        "CS":  GPIO_5,
        "CLK": GPIO_3
    }
    
    for name, pin in matrix_pins.items():
        print(f"   Testando {name} (GPIO {pin.pin()})...")
        pin.on()
        time.sleep(0.2)
        pin.off()
        time.sleep(0.1)

def led_status_pattern():
    """Usa o GPIO_2 como LED de status com padrões"""
    print("\nTestando GPIO_2 como LED de status...")
    
    # Padrão de inicialização
    for _ in range(3):
        GPIO_2.on()
        time.sleep(0.2)
        GPIO_2.off()
        time.sleep(0.2)
    
    # Padrão de funcionamento
    for _ in range(5):
        GPIO_2.on()
        time.sleep(0.1)
        GPIO_2.off()
        time.sleep(0.1)
    
    # Padrão de conclusão
    for _ in range(2):
        GPIO_2.on()
        time.sleep(0.5)
        GPIO_2.off()
        time.sleep(0.2)

# Executa os testes
if __name__ == "__main__":
    print("=== TESTE DOS GPIOs DISPONÍVEIS NO RP2040 ===")
    print("GPIOs disponíveis: 29, 28, 5, 4, 3, 2")
    print("=" * 50)
    
    try:
        test_gpio_sequence()
        test_display_pins()
        led_status_pattern()
        
        print("\n" + "=" * 50)
        print("Todos os testes concluídos com sucesso!")
        print("Os GPIOs estão funcionando corretamente.")
        
    except Exception as e:
        print(f"\nErro durante o teste: {e}")
        print("Verifique as conexões dos GPIOs.") 