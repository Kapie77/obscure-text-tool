Tenha o Python instalado, abra o cmd no diretório da ferramenta e digite:
```python extractor.py texwii_wii.dic```

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

## Observação:
Decodificação incorreta do layout de tiles resulta em:
- imagens embaralhadas
- duplicação
- artefatos visuais
