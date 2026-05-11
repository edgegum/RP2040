# RP2040 / Thonny Context

## Workspace

O workspace principal e `C:\Users\Luis Henrique\moises\Eduardo.code-workspace`.

Pastas do workspace:

- `web-moises`: `moises-1`
- `python`: `python_projects`
- `lua`: `lua_project`
- `rust`: `rust_projects`

Para trabalhos com Thonny/RP2040, usar a pasta `python_projects`.

## Arquivos RP2040 mais relevantes

- `iot/rp_dht11.py`: leitura DHT11/DHT22 em MicroPython usando PIO no RP2040.
- `test_ds18b20.py`: leitura de sensor DS18B20 via OneWire no GPIO28.
- `rp2040_gpio_test.py`: teste de GPIOs 29, 28, 5, 4, 3 e 2.
- `rp2040.py`: variante maior do DHT com tentativa de plot em Matplotlib; mistura MicroPython com CPython e deve ser tratada com cuidado.
- `wifi_scanner_rp2040.py`: candidato RP2040 para Wi-Fi/scan.
- `pwm_test_rp2040.py`, `pwm_plotter_rp2040.py`, `pulse_analyzer_rp2040.py`, `oscilloscope_rp2040.py`: scripts de medicao/sinal.
- `tracer_rp2040.py` e `tracer_rp2040.md`: contexto do tracador de curvas.
- `transistor_tracer_rp2040.py`: candidato para evolucao do tracador.

## Hardware e pinagem recorrente

- DHT11/DHT22: GPIO28, com pull-up.
- DS18B20: GPIO28, OneWire, resistor pull-up de 4.7k.
- Display TFT 1.14 SPI citado no analisador de pulso:
  - BL: GPIO13
  - DC: GPIO8
  - RST: GPIO12
  - MOSI: GPIO11
  - SCK: GPIO10
  - CS: GPIO9
- Entrada de pulso: GPIO28.
- PWM auxiliar: GPIO16.
- GPIOs usados em testes/display: 29, 28, 5, 4, 3, 2.

## Cuidados ao editar

- Distinguir scripts MicroPython de scripts CPython.
- MicroPython no RP2040 pode usar `machine`, `rp2`, `utime`, `onewire`, `ds18x20`.
- Scripts para rodar no PC podem usar `matplotlib`, `serial`, `time`, etc.
- Evitar misturar dependencias CPython em arquivos que devem rodar no Thonny/Pico.
- Para upload via Thonny, preferir arquivos simples e autocontidos.
- Validacao de sintaxe com CPython pode falhar em arquivos MicroPython que importam `machine`/`rp2`; usar como checagem limitada.

## Organizacao desejada

- Manter contexto de cada linha de experimento em `.md`.
- Antes de mexer em scripts RP2040, identificar se o alvo e:
  - sensor;
  - display;
  - comunicacao serial;
  - PWM/ADC;
  - tracador de curvas;
  - analisador de pulso.
- Evitar varrer `.venv`, `venv`, `__pycache__`, projetos de iPad e emuladores quando o pedido for RP2040/Thonny.

## Estado inicial recuperado

O workspace Python tem muitos projetos misturados. O foco RP2040/Thonny esta principalmente nos arquivos com `rp2040`, `dht`, `ds18b20`, `pwm`, `pulse`, `tracer`, `oscilloscope` e `wifi_scanner_rp2040`.

O arquivo `tracer_rp2040.md` registra que o teste PWM+ADC ainda nao representa uma curva real de transistor; para isso e necessario circuito com DUT, resistores de shunt e varredura/medicao corretas.
