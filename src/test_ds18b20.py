from machine import Pin
import onewire
import ds18x20
import time

# Configuração do DS18B20
ds_pin = Pin(28)  # Pino conectado ao sensor
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

# Procura por sensores no barramento
print("Procurando sensores DS18B20...")
roms = ds_sensor.scan()

if not roms:
    print("Nenhum sensor DS18B20 encontrado!")
    print("Verifique as conexões:")
    print("- Pino de dados conectado ao GPIO28")
    print("- Resistor pull-up de 4.7kΩ entre o pino de dados e VCC")
    print("- Alimentação correta (3.3V a 5.5V)")
else:
    print(f"Encontrado(s) {len(roms)} sensor(es)")
    print("Iniciando leituras...")
    print("Pressione Ctrl+C para sair")
    
    try:
        while True:
            # Inicia a conversão de temperatura
            ds_sensor.convert_temp()
            # Aguarda a conversão (750ms para 12-bit)
            time.sleep_ms(750)
            
            # Lê a temperatura de cada sensor encontrado
            for rom in roms:
                temp = ds_sensor.read_temp(rom)
                print(f"Temperatura: {temp:.1f}°C")
            
            # Aguarda 2 segundos antes da próxima leitura
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nTeste finalizado")
    except Exception as e:
        print("Erro:", e) 