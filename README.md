Tenha o Python e Pillow instalados, abra o cmd no diretório da ferramenta e digite:

Extract:
```bash
python obscure_texture_tool.py NomeDaTextura.Formato(, dic, .dip, .hvt, .hvi ou .xbr)
```

Rebuild:
```bash
python obscure_texture_tool.py NomeDaTextura.Formato --rebuild PastaDasTexturas/
```
rebuild de .dip de pc = ok
--
rebuild .dic de pc = ok
--
rebuild .dic de ps2 = ok
--
rebuild .dic de psp = ok
--
rebuild .dic de wii = ok
--
rebuild .xbr de xbox = ok
--
rebuild .hvt de pc/ps3/xbox 360 = em andamento
--
rebuild .hvi de ps2 = ok
--
rebuild .hvi de psp = ok
--
rebuild de .hvt de wii = ok
--

# Supported Games

| Game                     | Status | Platforms                        |
|--------------------------|:------:|----------------------------------|
| Obscure 1                |   ✅   | PC Steam (.dip) GOG (.dip) Retail (.dip), PS2 (.dic, .hvi), Xbox (.xbr)                 |
| Obscure 2                |   ✅   | PC Steam (.dic) Retail (.dic), PS2 (.dic, .hvi), Wii (.dic, .hvt), PSP (.dic, .hvi)                |
| Final Exam                |   ✅   | PC Steam (.hvt), Xbox (.hvt), PS3 (.hvt)              |

# ObsCure 1 e 2
## (Wii)
As texturas neste jogo utilizam o formato nativo do Wii (GX), que armazena imagens em blocos (tiles) em vez de formato linear.

### Arquivos suportados:
- `.dic`
- `.hvt`

### Formatos suportados:
- **CMPR (S3TW)** – compressão tipo DXT1 usada pelo Wii/GameCube
- **C4 (4bpp)** – usa paleta de 16 cores
- **C8 / P8WI (8bpp)** – usa paleta de 256 cores
- **RGB5A3 / 4443** – cor direta com alpha opcional
- **IA8 / G8A8** – intensidade + alpha
- **I8 / GRY8** – grayscale 8-bit
- **RGBA8 / ARGB** – cor completa 32-bit

### Características importantes:
- Texturas são armazenadas em tiles (blocos)
- Ordem dos pixels não é linear
- É necessário aplicar um cálculo de offset por tile para reconstruir a imagem
- Alguns formatos utilizam swizzle específico do hardware do Wii/GameCube

### Layout de tiles:
Os formatos utilizam diferentes tamanhos de bloco internos:

| BPP | Tile Size |
|---|---|
| 4bpp | 8x8 |
| 8bpp | 8x4 |
| 16bpp | 4x4 |
| 32bpp | 4x4 |

### Paletas:
- Armazenadas após os dados da textura
- `.dic` geralmente usa RGB565
- `.hvt` C8/P8WI utiliza RGB5A3 big-endian
- Paletas possuem normalmente 256 entradas (512 bytes)

### CMPR (S3TW)
O formato CMPR utilizado pelo Wii é similar ao DXT1, porém:
- usa ordem de bytes diferente
- utiliza layout em superblocos 8x8
- possui organização específica do GameCube/Wii

Cada superbloco contém:
- 4 sub-blocos 4x4
- 8 bytes por sub-bloco
- 32 bytes totais por tile 8x8

### RGBA32 (ARGB)
O formato RGBA32 do Wii não é linear:
- os canais são separados em dois grupos
- metade do tile contém AR
- a outra metade contém GB

### Caso especial: texturas tipo a_medallion
Algumas texturas (ex: a_medallion001, a_medallion002, fx_npc_die, fx_elec_bolt) utilizam um layout ligeiramente diferente do padrão.

**Diferenças:**
- Offset dos dados:
```python
data_offset = p + 24

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
| 0x07                |   SZ_X8R8G8B8  | 32 bpp (RGB, swizzled)                |
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

## (PS2) 
### .dic
**Características**
- Little-endian
- Baseado em RenderWare TXD
- Estrutura em chunks (RW_TEXTURE_DICTIONARY, RW_TEXTURE_NATIVE, RW_STRUCT, RW_STRING)
- Múltiplas texturas por arquivo
- Texturas indexed usam swizzling PS2 (CSM1)
- Algumas texturas usam palette RGB5551, outras RGBA8888
- Alpha de RGBA8888 usa faixa PS2 (0–128)

**Formatos de pixel suportados**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 4                |   PAL4  | 4 bpp indexed (swizzled)               |
| 8                |   PAL8  | 8 bpp indexed (swizzled)             |
| 16                |   RGB5551  | 16 bpp linear                |
| 32                |   RGBA8888  | 32 bpp linear                |

**Notas**
- Swizzle usa padrão de VRAM do PS2
- PAL8 utiliza remap de CLUT (CSM1)
- PAL4 não utiliza remap de palette
- Palettes podem existir em:
  - RGB5551
  - RGBA8888
- Alpha RGBA8888 precisa ser multiplicado por 2 ao decodificar
- Ao reimportar RGBA8888:
  - alpha precisa voltar para faixa 0–128
- Estrutura típica:
  - RW_TEXTURE_DICTIONARY
    - RW_TEXTURE_NATIVE
      - RW_STRING (nome)
      - RW_STRUCT (dados reais da textura)

### .hvi
**Características**
- Little-endian
- Textura única por arquivo
- Estrutura simples e linear
- Payload indexed já vem linearizado (sem swizzle)
- Palette armazenada em BGRA8888
- Alpha frequentemente usa faixa PS2 reduzida

**Formatos de pixel suportados**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 8                |   PAL8  | 8 bpp indexed               |
| BGRA8888                |   Palette  | CLUT BGRA8888             |

**Notas**
- Dados indexed não usam swizzling
- Palette usa ordem BGRA
- Algumas palettes usam alpha reduzido:
  - normalmente até 0x80 ou 0x90
- Ao decodificar:
  - alpha precisa ser multiplicado por 2 em alguns arquivos
- Estrutura típica:
  - Header
  - Palette BGRA8888
  - Indexed payload linear

## (PSP) .dic
**Características**
- Little-endian
- Múltiplas texturas por arquivo
- Estrutura sequencial simples (sem chunks RenderWare)
- Texturas indexadas usam swizzling em blocos PSP
- Palettes / CLUT armazenadas em RGBA8888
- Padding fixo de 4 bytes entre palette e imagem
- Algumas texturas usam RGBA8888 direto (sem palette)

**Formatos de pixel suportados**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| GU_PSM_T4                |   PAL4  | 4 bpp indexed (swizzled)  |
| GU_PSM_T8                |   PAL8  | 8 bpp indexed (swizzled)  |
| 32               |   RGBA8888  | 32 bpp linear  |

**Notas**
- Texturas indexed usam CLUT RGBA8888
- Payload indexed é armazenado em ordem swizzled do PSP
- Swizzle usa blocos 16x8 bytes
- Existe padding de 4 bytes após a palette, mesmo quando palette_size = 0
- RGBA8888 não usa swizzling
- Não utiliza RenderWare TXD (diferente do PS2)
- Estrutura básica:
  - Header da textura
  - Palette / CLUT
  - Padding (4 bytes)
  - Dados da imagem
    
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
