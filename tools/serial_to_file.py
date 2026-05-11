import serial

PORTA = 'COM8'  # Altere para a porta correta do seu RP2040
BAUD = 115200

ser = serial.Serial(PORTA, BAUD, timeout=1)
with open('buffer.txt', 'w') as f:
    print("Gravando dados da serial em buffer.txt...")
    while True:
        linha = ser.readline().decode(errors='ignore')
        if linha:
            f.write(linha)
            f.flush() 