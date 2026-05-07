Tenha o Python e Pillow instalados, abra o cmd no diretório da ferramenta e digite:

```python extractor.py NomeDaTextura.Formato(, dic, .dip, .hvt, .hvi ou .xbr)```

Falta suporte para Final Exam de PS3, consertar suporte do Obscure 2 .dic de PS2, e dar suporte para PSP do Obscure 2.

# Supported Games

| Game                     | Status | Platforms                        |
|--------------------------|:------:|----------------------------------|
| Obscure 1                |   ✅   | PC Steam (.dip) GOG (.dip) Retail (.dip), PS2 (.dic, .hvi), Xbox (.xbr)                 |
| Obscure 2                |   ✅   | PC Steam (.dic) Retail (.dic), PS2 (.dic, .hvi), Wii (.hvt)                |
| Final Exam                |   ✅   | PC Steam (.hvt), Xbox (.hvt), PS3 (.hvt)              |

# ObsCure 1 e 2
## (Wii)
As texturas neste jogo utilizam o formato nativo do Wii (GX), que armazena imagens em blocos (tiles) em vez de formato linear.

### Formatos suportados:
- **C4 (4bpp)** – usa paleta de 16 cores
- **C8 (8bpp)** – usa paleta de 256 cores
- **RGB5A3** – cor direta com alpha opcional
- **RGBA8** – cor completa 32-bit

### Características importantes:
- Texturas são armazenadas em tiles (blocos)
- Ordem dos pixels não é linear
- É necessário aplicar um cálculo de offset por tile para reconstruir a imagem

### Paletas:
- Armazenadas após os dados da textura
- Formato mais comum: RGB565

### Caso especial: texturas tipo a_medallion
Algumas texturas (ex: a_medallion001, a_medallion002, fx_npc_die, fx_elec_bolt) utilizam um layout ligeiramente diferente do padrão.

**Diferenças:**
- Offset dos dados:
```data_offset = p + 24```
(em vez de p + 28)

- Formato:
```GX = 8 (C4)```

- Paleta:
```RGB565 (pal_format = 1)```

### Observação:
Decodificação incorreta do layout de tiles resulta em:
- imagens embaralhadas
- duplicação
- artefatos visuais

## (PC)
O Obscure 1 usa .dip e o Obscure 2 usa .dic (texture dictionaries). Ambos armazenam múltiplas texturas com mipmaps, mas diferem principalmente em endianness e ordem de canais de cor.

### .dic
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

## (Xbox)
As versões de ObsCure para o Xbox clássico utilizam arquivos .xbr como dicionários de textura.
Esse formato é baseado diretamente na GPU NV2A (derivada do NVIDIA), e segue padrões muito próximos do Direct3D da época. O formato .xbr é um texture dictionary usado para armazenar múltiplas texturas em um único arquivo.

### .xbr
**Características**
- Little-endian
- Pode conter múltiplas texturas
- Suporta mipmaps
- Strings em ASCII
- Baseado no formato NV2A (Direct3D-like)
- Usa swizzle Morton (Z-order) em texturas SZ_*
- Estrutura com descriptors + tabela de nomes + bloco de pixels

**Formatos de pixel suportados**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 0x05                |   SZ_R5G6B5  | 16 bpp (RGB, swizzled)               |
| 0x02                |   SZ_A1R5G5B5  | 16 bpp (1-bit alpha, swizzled)             |
| 0x06                |   SZ_A8R8G8B8  | 32 bpp (RGBA, swizzled)                |
| 0x07                |   SZ_X8R8G8B8  | 32 bpp (RGB, swizzled))                |
| 0x11                |   LU_R5G6B5  | 16 bpp (linear)                |
| 0x12                |   LU_A8R8G8B8  | 32 bpp (linear)                |
| 0x13                |   LU_X8R8G8B8  | 32 bpp (linear)                |

**Formatos não suportados (comuns)**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 0x0C                |   DXT1  | Compressão S3TC               |
| 0x0E                |   DXT3  | Compressão com alpha             |
| 0x0F                |   DXT5  | Compressão avançada                |

**Observação:**
- Diferente do PS2, não usa paletas (CLUT)
- Mais próximo de APIs modernas (Direct3D)

# Final Exam
O Final Exam usa o formato .hvt (HydraVision modern), diferente do usado nos jogos Obscure clássicos. Ele armazena texturas standalone com suporte a múltiplas plataformas (PC, PS3, Xbox 360), variando principalmente em endianness, compressão e layout de memória.

## (PC) .hvt
**Características**
- Little-endian
- Textura única por arquivo
- Suporta mipmaps
- Header baseado em chunks (HEAD, DATA)
- Formatos de pixel identificados por tags ASCII (invertidas em alguns casos)
- Estrutura moderna comparada aos formatos antigos da HydraVision

**Formatos de pixel suportados**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| BGRA                |   BGRA  | 32 bpp (linear, com alpha)               |
| BGRX                |   BGRX  | 32 bpp (alpha forçado opaco)             |
| 1TXD                |   DXT1 (BC1)  | 4 bpp (compressão sem alpha ou 1-bit alpha)                |
| 3TXD                |   DXT3 (BC2)  | 8 bpp (alpha explícito 4-bit)                |
| 5TXD                |   DXT5 (BC3)  | 8 bpp (alpha interpolado)                |

**Notas**
- Tags como 1TXD, 3TXD, 5TXD são DXT1/3/5 invertidos (armazenados ao contrário no PC)
- Dados BC (DXT) são armazenados em little-endian padrão de PC
- Não há swizzling ou tiling (diferente do Xbox 360)
- BGRX ignora o canal alpha (sempre tratado como 255)
- Estrutura usa:
  - HEAD → metadados
  - DATA → dados da textura (mip0 primeiro)
 
## (Xbox) .hvt
**Características**
- Big-endian
- Textura única por arquivo
- Suporta mipmaps
- Header baseado em chunks (HEAD, X360, DATA)
- Usa tiling (swizzle de GPU) obrigatório
- Requer byte swap (16-bit) antes do decode
- Estrutura semelhante ao PS3, mas com layout de memória diferente (tiled)
- Dados podem conter padding (alinhamento)

**Formatos de pixel suportados**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| DXT1 / 1TXD                |   DXT1 (BC1)  | 4 bpp (compressão sem alpha ou 1-bit alpha)               |
| DXT3 / 3TXD                |   DXT3 (BC2)  | 8 bpp (alpha explícito 4-bit)             |
| DXT5 / 5TXD                |   DXT5 (BC3)  | 8 bpp (alpha interpolado)                |
| ARGB                |   ARGB  | 32 bpp (com alpha)                |

**Notas**

**Diferente do PC:**
- ✔ PC = dados lineares
- ❗ X360 = dados tiled (swizzled)
  
**Texturas precisam passar por:**
- unswizzle (reorganização de memória GPU)
- byte swap (endianness)
  
**Alinhamento obrigatório:**
- BC (DXT): múltiplos de 128 pixels
- ARGB: múltiplos de 32 pixels
  
**Após decodificação, é necessário:**
- remover padding (crop) para o tamanho original
  
**Dados BC usam blocos padrão (DXT), mas:**
- ❗ não estão em ordem linear
**Alguns arquivos podem conter:**
- bytes extras após o mip0
  
**Estrutura interna:**
- HEAD → metadados
- X360 → configuração GPU (tiling)
- DATA → dados da textura
  
**Tags podem aparecer como:**
- DXT1 / DXT5 (normal)
- 1TXD / 5TXD (variação)
