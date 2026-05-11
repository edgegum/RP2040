# Resumo Técnico – Traçador de Curvas com RP2040

## 1. Teste de PWM e ADC
- Script (`pwm_test_rp2040.py`) varre PWM nos pinos GPIO2 e GPIO3 do RP2040, lendo tensões nos ADC28 e ADC29.
- O display mostra curvas (verde e azul) que representam a resposta do sistema PWM+ADC, mas **não são curvas de transistor** – são praticamente lineares se não houver carga ativa.

## 2. Traçador de Curvas de Transistor
- O objetivo de um traçador de curvas é mostrar, por exemplo, **Ic x Vce** ou **Ic x Vbc** para diferentes valores de Ib.
- Para isso, o hardware deve excitar o transistor corretamente (varrendo Vce ou Vbc, controlando Ib) e medir Ic (usando resistor de shunt no coletor, por exemplo).
- O script deve implementar a varredura dupla (para cada Ib, varrer Vce ou Vbc e medir Ic) e plotar múltiplas curvas no display.

## 3. Sobre Ic x Vbc
- Se o PWM for usado para varrer Vbc (tensão base-coletor) e o ADC medir Ic, é possível traçar a curva Ic x Vbc.
- O script de varredura PWM+ADC pode ser adaptado para isso, **desde que o hardware esteja corretamente conectado**.

## 4. Pontos Importantes
- As curvas do teste PWM puro **não representam** as características de um transistor.
- Para ver as curvas corretas, é necessário:
  - Montar o circuito de traçador de curvas (com transistor e resistores de shunt).
  - Adaptar o script para varrer e medir os pontos corretos.
- Você vai testar com um transistor real para validar o funcionamento.

## 5. Continuação
- O contexto não é salvo automaticamente entre sessões. Recomenda-se salvar este resumo.
- Quando quiser retomar, basta colar este texto na próxima conversa.

## 6. Considerações Práticas sobre PWM, Capacitor e Descarga

- O capacitor no filtro RC é essencial para transformar o PWM em tensão DC, mas a tensão resultante sempre terá degraus, pois o PWM é ajustado em passos discretos.
- A corrente de base (Ib) e a tensão de coletor (Vc) variam em degraus conforme o PWM, mas podem se aproximar de uma rampa contínua se os passos forem pequenos e o filtro RC for eficiente.
- Para garantir que a tensão no coletor (ou base) realmente caia a zero entre varreduras, é importante prever um mecanismo de descarga do capacitor (por exemplo, usando um resistor de valor adequado ou um GPIO para descarregar ativamente).
- O mesmo vale para o filtro RC da base: é preciso garantir que Ib comece de zero em cada ciclo de varredura.
- A automação da varredura é poderosa, mas o entendimento físico do circuito (carga/descarga do capacitor, resposta do transistor, limitações do PWM, etc.) é fundamental para interpretar corretamente os resultados.
- Essas considerações são importantes para o próximo passo, quando forem acrescentados os resistores, capacitores e o DUT (Dispositivo sob Teste) ao circuito. 