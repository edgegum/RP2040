from machine import Pin, PWM, ADC, SPI
import time
import array
import framebuf

# Configuração do display TFT
BL = 13
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

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

class PWMTest:
    def __init__(self):
        # Configuração dos pinos
        self.gpio2 = Pin(2, Pin.OUT)  # PWM para teste
        self.gpio3 = Pin(3, Pin.OUT)  # PWM para teste
        self.adc28 = ADC(28)          # Medição PWM2
        self.adc29 = ADC(29)          # Medição PWM3
        
        # Configuração PWM
        self.pwm2 = PWM(self.gpio2)
        self.pwm3 = PWM(self.gpio3)
        self.pwm2.freq(1000)  # 1kHz
        self.pwm3.freq(1000)  # 1kHz
        
        # Configurações de medição
        self.v_max = 3.3    # Tensão máxima (3.3V do RP2040)
        self.voltage_buffer = array.array('f', [0] * 5)  # Buffer para filtro
        
        # Inicializa display
        self.lcd = LCD_1inch14()
        self.pwm = PWM(Pin(BL))
        self.pwm.freq(1000)
        self.pwm.duty_u16(32768)  # 50% de brilho
        
        # Inicializa com tensões zero
        self._set_voltage(0)
        
    def _set_voltage(self, voltage):
        """Define tensão de forma segura"""
        # Converte tensão para valor PWM (0-65535)
        pwm_value = int(voltage * 65535 / 3.3)
        
        # Aplica gradualmente
        current_pwm = self.pwm2.duty_u16()
        step = 100 if pwm_value > current_pwm else -100
        
        while current_pwm != pwm_value:
            current_pwm += step
            if (step > 0 and current_pwm > pwm_value) or \
               (step < 0 and current_pwm < pwm_value):
                current_pwm = pwm_value
            self.pwm2.duty_u16(current_pwm)
            self.pwm3.duty_u16(current_pwm)  # Aplica o mesmo valor ao PWM3
            time.sleep_ms(1)
    
    def _filter_reading(self, value, buffer):
        """Filtro de média móvel com rejeição de outliers"""
        # Adiciona novo valor ao buffer
        for i in range(len(buffer)-1):
            buffer[i] = buffer[i+1]
        buffer[-1] = value
        
        # Remove outliers
        sorted_buffer = sorted(buffer)
        if len(sorted_buffer) > 2:
            filtered = sorted_buffer[1:-1]  # Remove min e max
        else:
            filtered = sorted_buffer
            
        return sum(filtered) / len(filtered)
    
    def _update_display(self, pwm_values, adc28_values, adc29_values, current_pwm=None):
        """Atualiza o display com as curvas"""
        # Limpa o display
        self.lcd.fill(colour(0,0,0))
        
        # Desenha eixos
        self.lcd.line(20, 120, 220, 120, colour(255,255,255))  # Eixo X
        self.lcd.line(20, 20, 20, 120, colour(255,255,255))    # Eixo Y
        
        # Desenha grade
        for x in range(20, 221, 40):
            self.lcd.line(x, 20, x, 120, colour(64,64,64))
        for y in range(20, 121, 20):
            self.lcd.line(20, y, 220, y, colour(64,64,64))
        
        # Desenha curva PWM2 (verde)
        if len(pwm_values) > 1:
            for i in range(len(pwm_values)-1):
                try:
                    x1 = int(20 + (float(pwm_values[i]) / 65535) * 200)
                    y1 = int(120 - (float(adc28_values[i]) / self.v_max) * 100)
                    x2 = int(20 + (float(pwm_values[i+1]) / 65535) * 200)
                    y2 = int(120 - (float(adc28_values[i+1]) / self.v_max) * 100)
                    self.lcd.line(x1, y1, x2, y2, colour(0,255,0))
                except (TypeError, ValueError):
                    continue
        
        # Desenha curva PWM3 (azul)
        if len(pwm_values) > 1:
            for i in range(len(pwm_values)-1):
                try:
                    x1 = int(20 + (float(pwm_values[i]) / 65535) * 200)
                    y1 = int(120 - (float(adc29_values[i]) / self.v_max) * 100)
                    x2 = int(20 + (float(pwm_values[i+1]) / 65535) * 200)
                    y2 = int(120 - (float(adc29_values[i+1]) / self.v_max) * 100)
                    self.lcd.line(x1, y1, x2, y2, colour(0,0,255))
                except (TypeError, ValueError):
                    continue
        
        # Desenha ponto atual
        if current_pwm is not None:
            try:
                x = int(20 + (float(current_pwm) / 65535) * 200)
                y = int(120 - (float(self.adc28.read_u16()) * 3.3 / 65535 / self.v_max) * 100)
                self.lcd.fill_rect(x-2, y-2, 5, 5, colour(255,0,0))
            except (TypeError, ValueError):
                pass
        
        # Desenha valores
        try:
            pwm_percent = float(current_pwm)/65535*100 if current_pwm is not None else 0
            adc28_voltage = float(self.adc28.read_u16())*3.3/65535
            adc29_voltage = float(self.adc29.read_u16())*3.3/65535
            self.lcd.text(f"PWM: {pwm_percent:.1f}%", 30, 10, colour(255,255,255))
            self.lcd.text(f"ADC28: {adc28_voltage:.2f}V", 30, 130, colour(0,255,0))
            self.lcd.text(f"ADC29: {adc29_voltage:.2f}V", 120, 130, colour(0,0,255))
        except (TypeError, ValueError):
            self.lcd.text("Erro na leitura", 30, 10, colour(255,0,0))
        
        # Atualiza display
        self.lcd.show()
    
    def test_pwm(self, steps=500):
        """Testa os PWMs e ADCs"""
        self.lcd.fill(colour(0,0,0))
        self.lcd.text("Testando PWM...", 30, 60, colour(255,255,255))
        self.lcd.show()
        
        # Arrays para armazenar dados
        pwm_values = []
        adc28_values = []
        adc29_values = []
        
        # Varre PWM
        for pwm in range(steps):
            pwm_value = int((pwm / steps) * 65535)
            self._set_voltage(pwm_value * 3.3 / 65535)
            
            # Aguarda estabilização
            time.sleep_ms(20)  # Aumentado para 20 ms
            
            # Mede e filtra leituras
            adc28_reading = self._filter_reading(
                self.adc28.read_u16() * 3.3 / 65535,
                self.voltage_buffer
            )
            adc29_reading = self._filter_reading(
                self.adc29.read_u16() * 3.3 / 65535,
                self.voltage_buffer
            )
            
            # Armazena dados
            pwm_values.append(pwm_value)
            adc28_values.append(adc28_reading)
            adc29_values.append(adc29_reading)
            
            # Atualiza display
            self._update_display(pwm_values, adc28_values, adc29_values, pwm_value)
        
        # Desliga saída
        self._set_voltage(0)
        
        return pwm_values, adc28_values, adc29_values

def main():
    # Cria e testa o PWM
    tester = PWMTest()
    
    try:
        # Testa os PWMs
        pwm_values, adc28_values, adc29_values = tester.test_pwm()
        
        # Mostra resultados finais
        tester._update_display(pwm_values, adc28_values, adc29_values)
        time.sleep_ms(5000)  # Mostra por 5 segundos
            
    except Exception as e:
        tester.lcd.fill(colour(0,0,0))
        tester.lcd.text(f"Erro: {str(e)}", 30, 60, colour(255,0,0))
        tester.lcd.show()
        time.sleep_ms(5000)
    finally:
        # Garante que a saída está desligada
        tester._set_voltage(0)

if __name__ == "__main__":
    main() 