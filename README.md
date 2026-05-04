Tenha o Python instalado, abra o cmd no diretório da ferramenta e digite:
```python extractor.py NomeDaTextura.dic(ou .hvt)```

## Supported Games

| Game                     | Status | Platforms                        |
|--------------------------|:------:|----------------------------------|
| Obscure 2                |   ✅   | PC (.dic), Wii (.dic, .hvt)                |

# (Wii)
As texturas neste jogo utilizam o formato nativo do Wii (GX), que armazena imagens em blocos (tiles) em vez de formato linear.

## Formatos suportados:
- **C4 (4bpp)** – usa paleta de 16 cores
- **C8 (8bpp)** – usa paleta de 256 cores
- **RGB5A3** – cor direta com alpha opcional
- **RGBA8** – cor completa 32-bit

## Características importantes:
- Texturas são armazenadas em tiles (blocos)
- Ordem dos pixels não é linear
- É necessário aplicar um cálculo de offset por tile para reconstruir a imagem

## Paletas:
- Armazenadas após os dados da textura
- Formato mais comum: RGB565

## Caso especial: texturas tipo a_medallion
Algumas texturas (ex: a_medallion001, a_medallion002, fx_npc_die, fx_elec_bolt) utilizam um layout ligeiramente diferente do padrão.

**Diferenças:**
- Offset dos dados:
```data_offset = p + 24```
(em vez de p + 28)

- Formato:
```GX = 8 (C4)```

- Paleta:
```RGB565 (pal_format = 1)```

## Observação:
Decodificação incorreta do layout de tiles resulta em:
- imagens embaralhadas
- duplicação
- artefatos visuais
