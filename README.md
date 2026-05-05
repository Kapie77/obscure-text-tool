Tenha o Python instalado, abra o cmd no diretório da ferramenta e digite:
```python extractor.py NomeDaTextura.dic(.hvt ou .dip)```

## Supported Games

| Game                     | Status | Platforms                        |
|--------------------------|:------:|----------------------------------|
| Obscure 1                |   ✅   | PC Steam (.dip) GOG (.dip) Retail (.dip) PS2 (.dic, .hvi)                 |
| Obscure 2                |   ✅   | PC Steam (.dic) Retail (.dic), PS2 (.dic, .hvi), Wii (.hvt)                |

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

# (PC)
O Obscure 1 usa .dip e o Obscure 2 usa .dic (texture dictionaries). Ambos armazenam múltiplas texturas com mipmaps, mas diferem principalmente em endianness e ordem de canais de cor.

## .dic
**Características**
- Big-endian
- Pode conter múltiplas texturas
- Suporta mipmaps
- Strings em Shift-JIS
- Formato semelhante ao usado em ferramentas como TexDict

**Formatos de pixel suportados**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 21                |   R8G8B8A8  | 32 bpp (RGBA)               |
| 23                |   R5G6B5  | 16 bpp (sem alpha)             |
| 25                |   R5G5B5A1  | 16 bpp (1-bit alpha)                |

## .dip
**Características**
- Little-endian
- Estrutura muito semelhante ao .dic
- Strings em ASCII
- Usado especificamente no Obscure 1 (PC)
- Baseado em scripts como fmt_dip.py (Noesis)

**Formatos de pixel suportados**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 21                |   B8G8R8A8  | 32 bpp (BGRA)               |
| 23                |   B5G6R5  | 16 bpp             |
| 25                |   B5G5R5A1  | 16 bpp (1-bit alpha)                |
