# Analisador de Pulso Digital para Raspberry Pi Pico
## Descrição
Este projeto implementa um analisador de pulso digital preciso usando o Raspberry Pi Pico e um display TFT 1.14" SPI. O sistema é capaz de medir com alta precisão (erro < 0.5%) a largura de pulsos digitais, especialmente útil para análise de sinais de controle, temporizações e debug de circuitos digitais.

## Características
- Medição precisa da largura do pulso em nível baixo (0V)
- Erro de medição inferior a 0.5%
- Visualização em tempo real da forma de onda
- Detecção automática de mudanças no pulso
- Geração de PWM sincronizado com o pulso medido
- Interface gráfica limpa e profissional
- Ajuste automático a variações no pulso

## Hardware Necessário
1. Raspberry Pi Pico
2. Display TFT 1.14" SPI
3. Conexões:
   - Display TFT:
     - BL (Backlight): GPIO13
     - DC (Data/Command): GPIO8
     - RST (Reset): GPIO12
     - MOSI: GPIO11
     - SCK: GPIO10
     - CS (Chip Select): GPIO9
   - Entrada do Pulso: GPIO28
   - Saída PWM: GPIO16

## Software
### Dependências
- MicroPython para Raspberry Pi Pico
- Bibliotecas padrão: machine, time, framebuf

### Estrutura do Código
1. **Classe LCD_1inch14**:
   - Controle do display TFT
   - Inicialização e configuração
   - Métodos de desenho e atualização

2. **Classe PulseAnalyzer**:
   - Medição do pulso via interrupção
   - Média móvel com filtro de outliers
   - Detecção de mudanças no pulso
   - Geração de PWM
   - Visualização em tempo real

### Funcionalidades Principais
1. **Medição de Pulso**:
   - Usa interrupções para detecção precisa
   - Mede o tempo em nível baixo (0V)
   - Implementa média móvel para suavização

2. **Detecção de Mudanças**:
   - Monitora variações > 10% no pulso
   - Reinicia medições após 3 mudanças consecutivas
   - Indica estado de ajuste na tela

3. **Visualização**:
   - Gráfico em tempo real (2/3 da tela)
   - Informações de medição (1/3 inferior)
   - Grade de referência
   - Indicador de estabilidade

4. **PWM Sincronizado**:
   - Frequência baseada no período medido
   - Duty cycle proporcional à largura do pulso
   - Tratamento de frequências muito baixas

## Como Usar
1. **Montagem**:
   - Conecte o display TFT conforme pinagem especificada
   - Conecte o sinal a ser medido ao GPIO28
   - (Opcional) Conecte o PWM ao GPIO16

2. **Operação**:
   - Carregue o script no Pico
   - O display mostrará "Ajustando..." durante a estabilização
   - Após estabilizar, mostrará:
     - Largura do pulso em ms
     - Período em ms
     - Frequência em Hz

3. **Interpretação**:
   - O gráfico mostra o pulso em tempo real
   - Valores são atualizados continuamente
   - Sistema se ajusta automaticamente a mudanças

## Limitações
- Frequência mínima do PWM: 1Hz
- Resolução temporal: 1μs
- Memória disponível para buffer: 240 pontos

## Possíveis Melhorias
1. Múltiplos canais de medição
2. Diferentes modos de trigger
3. Armazenamento de dados
4. Interface mais elaborada
5. Calibração automática

## Autor
Adaptado por IA para uso didático

## Licença
Este projeto é open source e pode ser usado livremente para fins educacionais e pessoais.

## Aplicações e Projetos Relacionados
Este analisador de pulso serve como base para diversos projetos mais complexos:

### 1. Eletrocardiograma (ECG)
- **Aplicação**: Monitoramento cardíaco
- **Adaptações Necessárias**:
  - Amplificação do sinal do sensor
  - Filtros para remoção de ruído
  - Algoritmos de detecção de complexos QRS
  - Cálculo de frequência cardíaca
  - Armazenamento de dados

### 2. Decodificador OOK (On-Off Keying)
- **Aplicação**: Comunicação digital sem fio
- **Adaptações Necessárias**:
  - Receptor RF (ex: módulo 433MHz)
  - Decodificação de protocolos (ex: Manchester)
  - Buffer para armazenamento de bits
  - Interface para transmissão de dados

### 3. Outras Possíveis Aplicações
- Análise de sensores de proximidade
- Monitoramento de encoders
- Debug de protocolos de comunicação
- Análise de temporizações em circuitos digitais

## Considerações para Projetos Futuros
1. **Eletrocardiograma**:
   - Necessidade de maior resolução temporal
   - Implementação de filtros digitais
   - Interface para exportação de dados
   - Algoritmos de análise de ritmo cardíaco

2. **Decodificador OOK**:
   - Otimização para altas frequências
   - Implementação de protocolos específicos
   - Buffer circular para dados recebidos
   - Interface serial para comunicação 