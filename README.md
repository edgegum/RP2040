# RP2040 MicroPython Scripts

Scripts em MicroPython para Raspberry Pi Pico/RP2040, usados com Thonny.

## Estrutura

- `src/`: scripts para rodar no Pico/Thonny.
- `src/iot/`: sensores e experimentos IoT.
- `tools/`: ferramentas de apoio para rodar no PC.
- `docs/`: contexto tecnico, pinagens e notas dos experimentos.

## Projetos principais

- DHT11/DHT22 via PIO: `src/iot/rp_dht11.py`
- DS18B20 via OneWire: `src/test_ds18b20.py`
- Teste de GPIO: `src/rp2040_gpio_test.py`
- PWM/ADC: `src/pwm_test_rp2040.py`, `src/pwm_plotter_rp2040.py`
- Analisador de pulso: `src/pulse_analyzer_rp2040.py`
- Osciloscopio simples: `src/oscilloscope_rp2040.py`
- ATtiny85 ISP via RP2040: `src/attiny_isp_signature_rp2040.py`, `src/attiny_isp_inspector_rp2040.py`, `src/attiny_isp_flash_writer_rp2040.py`
- Tracador de curvas: `src/tracer_rp2040.py`, `src/transistor_tracer_rp2040.py`
- Display/OLED/Nokia/Matrix: `src/display.py`, `src/oled2864.py`, `src/nokia5110_pcd8544_test.py`, `src/matrix8x8_bitbang.py`
- GPS/Bluetooth/RFID: `src/gps.py`, `src/bluetooth_test.py`, `src/rfid.py`

## Notas de uso

- Arquivos em `src/` normalmente esperam MicroPython no RP2040 e podem importar `machine`, `rp2`, `utime`, `onewire` ou `ds18x20`.
- Arquivos em `tools/` sao auxiliares para PC e podem depender de CPython, serial, matplotlib ou bibliotecas de desktop.
- Para carregar no Pico, abrir o script no Thonny e salvar/executar no dispositivo.

## Contexto

Ver `docs/RP2040_THONNY_CONTEXT.md` para pinagens recorrentes, cuidados de edicao e mapa dos scripts.

Notas do fluxo ATtiny85 ISP ficam em `docs/attiny_isp_rp2040_notes.md`.
