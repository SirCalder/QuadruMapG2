# QuadruMapG2

Sistema de aquisição e mapeamento GNSS (GPS) para robótica móvel, desenvolvido como parte de um Trabalho de Conclusão de Curso (TCC). O projeto combina um módulo GPS externo (Quectel L30) lido por um Arduino, com um pipeline em **ROS 2** rodando em uma plataforma embarcada (ex.: NVIDIA Jetson), responsável por validar a qualidade do sinal, publicar as posições e exportar a trajetória percorrida em formato **GeoJSON**.

## Visão geral da arquitetura

```
Módulo GNSS (Quectel L30)
        │  NMEA @ 4800 bps
        ▼
   Arduino (TCC_GNSS.ino)
        │  CSV @ 115200 bps  ->  Lat,Lon,Alt,Sat,HDOP,Data,Hora
        ▼  (Serial /dev/ttyACM0)
gnss_lifecycle_node.py (nó ROS 2 Lifecycle)
        │  Filtra por nº de satélites e HDOP
        │  Publica sensor_msgs/NavSatFix em /gps/fix
        ▼
simple_sig_exporter.py (nó ROS 2)
        │  Acumula coordenadas válidas
        ▼
   trajetoria_*.geojson (LineString da rota percorrida)
```

O sistema faz "edge computing": a validação do sinal (número de satélites e HDOP) acontece o mais cedo possível na cadeia, para que dados de baixa qualidade não cheguem a poluir o mapa final.

## Estrutura do repositório

| Arquivo | Descrição |
|---|---|
| `TCC_GNSS/TCC_GNSS.ino` | Firmware para Arduino (Elegoo Uno R3). Liga o módulo GNSS Quectel L30, decodifica as sentenças NMEA com a biblioteca `TinyGPS++` e envia os dados já formatados (CSV) pela porta serial para o computador de bordo. |
| `gnss_lifecycle_node.py` | Nó ROS 2 do tipo **Lifecycle Node**. Abre a porta serial, lê os dados enviados pelo Arduino, descarta leituras com poucos satélites ou HDOP alto, e publica mensagens `sensor_msgs/NavSatFix` no tópico `/gps/fix`. Se o sinal degradar de forma sustentada, o nó se autodesativa. |
| `simple_sig_exporter.py` | Nó ROS 2 que assina o tópico `/gps/fix`, acumula as coordenadas válidas recebidas e, ao ser encerrado (Ctrl+C), exporta a trajetória percorrida como um arquivo `.geojson` (LineString), pronto para ser aberto em ferramentas de SIG (QGIS, geojson.io etc.). |
| `ler_arduino.py` | Script simples de leitura contínua da porta serial, usado para depuração manual fora do ROS 2. |
| `teste_serial.py` | Script utilitário para testar rapidamente a conexão serial com o Arduino e diagnosticar problemas de porta/permissão. |
| `trajetoria_jettank_182230.geojson` | Exemplo de saída gerada pelo `simple_sig_exporter.py`. |

## Pré-requisitos

- **Hardware**
  - Arduino (testado com Elegoo Uno R3)
  - Módulo GNSS Quectel L30 (ou compatível NMEA)
  - Computador de bordo com ROS 2 instalado (ex.: NVIDIA Jetson)
- **Software**
  - [ROS 2](https://docs.ros.org/) (Humble ou superior recomendado)
  - Python 3 com o pacote `pyserial`
  - Arduino IDE com a biblioteca [`TinyGPS++`](https://github.com/mikalhart/TinyGPSPlus) instalada

Instalação das dependências Python:

```bash
pip install pyserial
```

## Como usar

### 1. Gravar o firmware no Arduino

Abra `TCC_GNSS/TCC_GNSS.ino` na Arduino IDE, ajuste os pinos se necessário (`RX_PIN`, `TX_PIN`, `WAKEUP_PIN`) e faça o upload para a placa. O Arduino passará a enviar linhas no formato:

```
Lat,Lon,Alt,Sat,HDOP,Data,Hora
```

### 2. (Opcional) Testar a comunicação serial

Antes de subir o ROS 2, é possível validar a conexão com o Arduino:

```bash
python3 teste_serial.py
# ou
python3 ler_arduino.py
```

### 3. Rodar o nó GNSS (ROS 2 Lifecycle Node)

```bash
ros2 run <seu_pacote> gnss_lifecycle_node.py
```

Parâmetros configuráveis (via `ros2 param` ou launch file):

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `serial_port` | `/dev/ttyACM0` | Porta serial do Arduino |
| `baudrate` | `115200` | Velocidade da comunicação serial |
| `frame_id` | `gps_link` | Frame de referência das mensagens `NavSatFix` |
| `min_satellites` | `4` | Número mínimo de satélites para considerar a leitura válida |
| `max_hdop` | `5.0` | HDOP máximo tolerado |
| `max_tolerated_errors` | `30` | Nº de leituras degradadas seguidas antes de desativar o nó automaticamente |

Como é um Lifecycle Node, é necessário transicioná-lo entre os estados `configure` e `activate`:

```bash
ros2 lifecycle set /gnss_edge_node configure
ros2 lifecycle set /gnss_edge_node activate
```

### 4. Rodar o exportador de trajetória

```bash
ros2 run <seu_pacote> simple_sig_exporter.py
```

O nó ficará escutando o tópico `/gps/fix`. Ao encerrar com `Ctrl+C`, ele salva automaticamente um arquivo `trajetoria_jettank_<HHMMSS>.geojson` contendo a rota percorrida como uma `LineString`.

## Formato de saída (GeoJSON)

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[-49.347274, -26.24769], ...]
      },
      "properties": {
        "name": "Trajetoria_JetTank",
        "pontos_validados": 123
      }
    }
  ]
}
```

O arquivo pode ser aberto diretamente em ferramentas como [QGIS](https://qgis.org/), [geojson.io](https://geojson.io/) ou qualquer biblioteca de mapas compatível com GeoJSON.

## Status do projeto

Este é um projeto acadêmico (TCC) em desenvolvimento. Contribuições, sugestões e issues são bem-vindas.

## Licença

Nenhuma licença foi definida ainda para este repositório.
