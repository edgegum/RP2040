from machine import UART, Pin
import time
from time import sleep

class BluetoothSerial:
    def __init__(self, uart_num=1, tx_pin=8, rx_pin=9, baudrate=9600):
        self.uart = UART(uart_num, baudrate=baudrate, tx=Pin(tx_pin), rx=Pin(rx_pin))
        self.uart_num = uart_num
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin
        self.baudrate = baudrate

    def clear_buffer(self):
        """Limpa o buffer de recepção"""
        while self.uart.any():
            self.uart.read()
        sleep(0.1)

    def send_message(self, message):
        """Envia uma mensagem pelo módulo Bluetooth/serial"""
        try:
            print(f"\nEnviando mensagem: {message}")
            self.clear_buffer()
            self.uart.write((message + '\r').encode())
            print("Mensagem enviada!")
            return True
        except Exception as e:
            print("\nErro ao enviar mensagem:", str(e))
            return False

    def receive_message(self, timeout=5):
        """Recebe uma mensagem do módulo Bluetooth/serial"""
        print("\nAguardando mensagem...")
        print(f"Tempo limite: {timeout} segundos")
        
        try:
            start_time = time.time()
            response_data = bytearray()
            
            while (time.time() - start_time) < timeout:
                if self.uart.any():
                    chunk = self.uart.read()
                    if chunk:
                        response_data.extend(chunk)
                        sleep(0.1)
                        continue
                
                if response_data:
                    print(f"\nMensagem recebida ({len(response_data)} bytes):")
                    print("Raw data:", repr(response_data))
                    try:
                        decoded = response_data.decode().strip()
                        print("Decodificado:", decoded)
                        return decoded
                    except UnicodeError:
                        print("Erro ao decodificar a mensagem")
                        return None
                
                sleep(0.1)
            
            print(f"\nNenhuma mensagem recebida no tempo limite de {timeout} segundos")
            return None
                
        except Exception as e:
            print("\nErro na comunicação:", str(e))
            return None

def main():
    print("Teste de Comunicação Serial")
    print("==========================")
    print("Conecte o módulo:")
    print("- VCC do módulo -> 3.3V do Pico")
    print("- GND do módulo -> GND do Pico")
    print("- TX do módulo  -> GP9 do Pico (RX)")
    print("- RX do módulo  -> GP8 do Pico (TX)")
    print("\nConfigurações:")
    print("- UART: 1")
    print("- Pinos: TX=GP8, RX=GP9")
    print("- Baudrate: 9600")
    
    # Inicializa o módulo
    bt = BluetoothSerial()
    
    while True:
        print("\nEscolha uma opção:")
        print("1 - Enviar mensagem")
        print("2 - Receber mensagem")
        print("3 - Sair")
        
        choice = input("\nSua escolha (1-3): ")
        
        if choice == "1":
            message = input("Digite a mensagem a ser enviada: ")
            bt.send_message(message)
        elif choice == "2":
            bt.receive_message()
        elif choice == "3":
            print("\nEncerrando programa...")
            break
        else:
            print("\nOpção inválida! Escolha 1, 2 ou 3.")

if __name__ == "__main__":
    main() 