# SabidosReceiver no Home Assistant

Integração MQTT para o firmware Tasmota personalizado com `driver129`, PT2322 e PT2323 opcional. O componente usa o domínio `monoprice_custom`, igual à pasta, sem substituir a integração Monoprice oficial.

## Instalação e migração

1. Faça backup da configuração do Home Assistant.
2. Copie `custom_components/monoprice_custom` para `/config/custom_components/monoprice_custom` e reinicie o Home Assistant. A integração MQTT deve estar configurada e conectada ao mesmo broker que o Tasmota.
3. Em **Configurações → Dispositivos e serviços → Adicionar integração**, procure **SabidosReceiver**.
4. Informe exatamente o `Topic` definido no Tasmota, por exemplo `tasmota_4232F0`. Não informe IP, porta, `cmnd/` ou `driver129`. A integração pressupõe FullTopic padrão `%prefix%/%topic%/` e o tópico de nascimento padrão `homeassistant/status`.
5. Habilite PT2323 apenas quando o firmware tiver esse suporte e a placa estiver equipada. Também pode habilitar/desabilitar depois em **Opções**.

Esta é uma atualização principal para 2.0. A versão anterior tinha pasta `monoprice_custom`, mas manifest/config flow usavam `monoprice`, além de um Topic fixo. Se houver uma instalação antiga funcionando após alterações manuais, remova sua entrada antiga, instale esta pasta e adicione SabidosReceiver novamente. Os identificadores das entidades mudam; revise dashboards e automações. Não exclua a integração Monoprice oficial caso controle outro equipamento.

## Controles

- Receiver: ligado/desligado, volume, mute e seleção de entrada quando PT2323 está habilitado.
- Números: níveis FL/FR/CT/SUB/SL/SR em **-15..0 dB** e graves/médios/agudos em **-14..+14 dB**, com passo de 2 dB.
- Switches: 3D e controle de tom do PT2322; opcionais PT2323 para surround, ganho misturado +6 dB, mute geral e seis mutes individuais.
- Select: 5.1, Stereo 1, Stereo 2, Stereo 3, Stereo 4.
- Sensores de diagnóstico: flags do PT2322 e erro I2C do PT2323; desabilitados inicialmente no registro de entidades.

O protocolo legado usa níveis de canal 0..15, mas a interface mostra os dB reais. Uma automação antiga que definia nível 15 passa a definir **0 dB**; nível 0 passa a **-15 dB**. O protocolo de tons é -7..7, convertido para dB na interface.

As flags `3D` e `Tone` do firmware indicam função **desativada**; os switches mostram função **ativada**. Nenhum controle inventa um valor após publicar: o estado só muda quando chega resposta/telemetria do dispositivo. A ausência do PT2323 não impede os controles PT2322.

Os controles sem suporte funcional no firmware anterior — balance, snapshot/restore e perfis de graves — foram retirados. Ajuste o tom pelos controles de graves/médios/agudos; não há serviços antigos fingindo funcionar.

## Comunicação

Uma assinatura compartilhada por equipamento recebe `stat/<Topic>/RESULT`, `tele/<Topic>/SENSOR` e `tele/<Topic>/LWT`. Comandos não retidos vão para `cmnd/<Topic>/driver129`. Ao receber Online ou o nascimento do Home Assistant, solicita o estado. As assinaturas são removidas ao descarregar a integração.

Com o firmware atualizado, PT2323 ausente ou falha de configuração deixa os controles opcionais indisponíveis. As respostas antigas abreviadas VL/FL/FR/CT/SB/RL/RR são normalizadas. FullTopic personalizado ainda não é suportado; use o padrão informado acima.

## Testes

`python3 -m unittest discover -s tests -v`

Os dez testes usam um simulador mínimo de HA/MQTT: parsing, lifecycle, tópicos configuráveis, LWT, reconexão, falhas, conversão de dB, máscara de mute e controles. Eles não substituem uma instalação real do Home Assistant e um teste em bancada. Versão mínima declarada: Home Assistant 2024.12.
