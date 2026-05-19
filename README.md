<h1 align="center">Obscure Texture Tool</h1>

<p align="center">
  <b>A cross-platform CLI for any version of Obscure 1, Obscure 2, and Final Exam.</b></br>
  <sub>I created this tool based on Heitor's <a href="https://github.com/HeitorSpectre/ObsCure-Texture-Editor">ObsCure Texture Editor</a>.</sub>
</p>

<div align="center">

</div>

<p align="center">
  <a href="#supported-games">Supported Games</a> •
  <a href="#how-to-use">How to use</a> •
  <a href="#obscure-1-e-2">ObsCure 1 e 2</a> •
  <a href="#final-exam">Final Exam</a> •
</p>

# Supported Games

| Game                     | Status | Versions                        |
|--------------------------|:------:|----------------------------------|
| Obscure 1                |   ✅   | PC Steam (.dip) GOG (.dip) Retail (.dip), PS2 (.dic, .hvi), Xbox (.xbr)                 |
| Obscure 2                |   ✅   | PC Steam (.dic) Retail (.dic), PS2 (.dic, .hvi), Wii (.dic, .hvt), PSP (.dic, .hvi)                |
| Final Exam                |   ✅   | PC Steam (.hvt), Xbox (.hvt), PS3 (.hvt)              |

# How to use
## Windows (Drag and Drop)
**Extract:**
Drag the *texture file* onto ```obscure_texturetool.exe``` and drop it.

**Rebuild:**
Drag the *texture file* and the *extracted folder* onto ```obscure_texturetool.exe``` and drop them there.

## Linux (CLI)
**Extract:**
```bash
obscure_texture_tool.exe extract TextureName.Format(, dic, .dip, .hvt, .hvi ou .xbr)
```

**Rebuild:**
```bash
obscure_texture_tool.exe rebuild TextureName.Format TextureFile/
```

# ObsCure 1 e 2
## (Wii)
The textures in this game use the Wii's native format (GX), which stores images in tiles rather than in a linear format.

### Supported file formats:
- `.dic`
- `.hvt`

### Supported formats:
- **CMPR (S3TW)** – DXT1 compression used by the Wii and GameCube
- **C4 (4bpp)** – uses a 16-color palette
- **C8 / P8WI (8bpp)** – uses a 256-color palette
- **RGB5A3 / 4443** – spot color with optional alpha
- **IA8 / G8A8** – intensity + alpha
- **I8 / GRY8** – grayscale 8-bit
- **RGBA8 / ARGB** – 32-bit full color

### Key features:
- Textures are stored in tiles
- The order of the pixels is not linear
- An offset calculation must be applied to each tile to reconstruct the image
- Some formats use a swizzle specific to the Wii/GameCube hardware

### Tile layout:
The formats use different internal block sizes:

| BPP | Tile Size |
|---|---|
| 4bpp | 8x8 |
| 8bpp | 8x4 |
| 16bpp | 4x4 |
| 32bpp | 4x4 |

### Palettes:
- Stored after the texture data
- `.dic` files typically use RGB565
- `.hvt` C8/P8WI files use big-endian RGB5A3
- Palettes usually have 256 entries (512 bytes)

### CMPR (S3TW)
The CMPR format used by the Wii is similar to DXT1, but:
- it uses a different byte order
- it uses an 8x8 superblock layout
- it has a specific GameCube/Wii organization

Each superblock contains:
- 4 4x4 subblocks
- 8 bytes per subblock
- 32 bytes total per 8x8 tile

### RGBA32 (ARGB)
The Wii's RGBA32 format is not linear:
- the channels are divided into two groups
- half of the tile contains AR
- the other half contains GB

### Special case: texture like a_medallion
Some textures (e.g., a_medallion001, a_medallion002, fx_npc_die, fx_elec_bolt) use a layout that differs slightly from the standard.

**Differences:**
- Data offset:
```python
data_offset = p + 24
```
(em vez de p + 28)
* Format:
```python
GX = 8 (C4)
```
* Palette
```python
RGB565 (pal_format = 1)
```

**HVT (Wii)**
Wii .hvt files have:
* a fixed header of 0x18
* magic:
```python
b" IVH"
```

**HVT format tags**
| Tag                     | Formato | 
|--------------------------|:------:|
| S3TW                |   CMPR  | 
| G8A8                |   IA8  |
| GRY8                |   I8  | 
| 4443                |   RGB5A3  |
| ARGB                |   RGBA32  |
| P8WI                |   C8  | 

**Features of HVTs:**
* width/height stored in big-endian format
* bpp stored in big-endian format
* may contain a palette + trailer
* trailers are automatically preserved during a rebuild

## (PC)
O Obscure 1 usa .dip e o Obscure 2 usa .dic (texture dictionaries). Ambos armazenam múltiplas texturas com mipmaps, mas diferem principalmente em endianness e ordem de canais de cor.

### .dic
**Features**
- Big-endian
- Pode conter múltiplas texturas
- Suporta mipmaps
- Strings em Shift-JIS
- Formato semelhante ao usado em ferramentas como TexDict

**Supported pixel formats**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 21                |   R8G8B8A8  | 32 bpp (RGBA)               |
| 23                |   R5G6B5  | 16 bpp (sem alpha)             |
| 25                |   R5G5B5A1  | 16 bpp (1-bit alpha)                |

## .dip
**Features**
- Little-endian
- Estrutura muito semelhante ao .dic
- Strings em ASCII
- Usado especificamente no Obscure 1 (PC)
- Baseado em scripts como fmt_dip.py (Noesis)

**Supported pixel formats**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 21                |   B8G8R8A8  | 32 bpp (BGRA)               |
| 23                |   B5G6R5  | 16 bpp             |
| 25                |   B5G5R5A1  | 16 bpp (1-bit alpha)                |

## (Xbox)
As versões de ObsCure para o Xbox clássico utilizam arquivos .xbr como dicionários de textura.
Esse formato é baseado diretamente na GPU NV2A (derivada do NVIDIA), e segue padrões muito próximos do Direct3D da época. O formato .xbr é um texture dictionary usado para armazenar múltiplas texturas em um único arquivo.

### .xbr
**Features**
- Little-endian
- Pode conter múltiplas texturas
- Suporta mipmaps
- Strings em ASCII
- Baseado no formato NV2A (Direct3D-like)
- Usa swizzle Morton (Z-order) em texturas SZ_*
- Estrutura com descriptors + tabela de nomes + bloco de pixels

**Supported pixel formats**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 0x05                |   SZ_R5G6B5  | 16 bpp (RGB, swizzled)               |
| 0x02                |   SZ_A1R5G5B5  | 16 bpp (1-bit alpha, swizzled)             |
| 0x06                |   SZ_A8R8G8B8  | 32 bpp (RGBA, swizzled)                |
| 0x07                |   SZ_X8R8G8B8  | 32 bpp (RGB, swizzled)                |
| 0x11                |   LU_R5G6B5  | 16 bpp (linear)                |
| 0x12                |   LU_A8R8G8B8  | 32 bpp (linear)                |
| 0x13                |   LU_X8R8G8B8  | 32 bpp (linear)                |

**Unsupported formats (common)**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 0x0C                |   DXT1  | Compressão S3TC               |
| 0x0E                |   DXT3  | Compressão com alpha             |
| 0x0F                |   DXT5  | Compressão avançada                |

**Note:**
- Diferente do PS2, não usa paletas (CLUT)
- Mais próximo de APIs modernas (Direct3D)

## (PS2) 
### .dic
**Features**
- Little-endian
- Baseado em RenderWare TXD
- Estrutura em chunks (RW_TEXTURE_DICTIONARY, RW_TEXTURE_NATIVE, RW_STRUCT, RW_STRING)
- Múltiplas texturas por arquivo
- Texturas indexed usam swizzling PS2 (CSM1)
- Algumas texturas usam palette RGB5551, outras RGBA8888
- Alpha de RGBA8888 usa faixa PS2 (0–128)

**Supported pixel formats**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 4                |   PAL4  | 4 bpp indexed (swizzled)               |
| 8                |   PAL8  | 8 bpp indexed (swizzled)             |
| 16                |   RGB5551  | 16 bpp linear                |
| 32                |   RGBA8888  | 32 bpp linear                |

**Notes**
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
**Features**
- Little-endian
- Textura única por arquivo
- Estrutura simples e linear
- Payload indexed já vem linearizado (sem swizzle)
- Palette armazenada em BGRA8888
- Alpha frequentemente usa faixa PS2 reduzida

**Supported pixel formats**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| 8                |   PAL8  | 8 bpp indexed               |
| BGRA8888                |   Palette  | CLUT BGRA8888             |

**Notes**
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
**Features**
- Little-endian
- Múltiplas texturas por arquivo
- Estrutura sequencial simples (sem chunks RenderWare)
- Texturas indexadas usam swizzling em blocos PSP
- Palettes / CLUT armazenadas em RGBA8888
- Padding fixo de 4 bytes entre palette e imagem
- Algumas texturas usam RGBA8888 direto (sem palette)

**Supported pixel formats**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| GU_PSM_T4                |   PAL4  | 4 bpp indexed (swizzled)  |
| GU_PSM_T8                |   PAL8  | 8 bpp indexed (swizzled)  |
| 32               |   RGBA8888  | 32 bpp linear  |

**Notes**
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

## (PSP) .hvt
**Features**
- Little-endian
- Arquivo contém textura única
- Estrutura simples sem containers RenderWare
- Dados de imagem armazenados em formato PSP swizzled
- Alguns arquivos usam CLUT / palettes
- Compatível com texturas de interface e HUD do ObsCure Final Exam PSP
- Header compacto com dimensões e formato de pixel

**Supported pixel formats**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| GU_PSM_T4                | PAL4 | 4 bpp indexed (swizzled) |
| GU_PSM_T8                | PAL8 | 8 bpp indexed (swizzled) |
| GU_PSM_8888              | RGBA8888 | 32 bpp linear |

**Notes**
- Texturas indexed utilizam palettes / CLUT RGBA8888
- Payload indexed usa swizzle padrão do PSP
- Swizzle do PSP usa blocos 16x8 bytes
- RGBA8888 é armazenado linearmente
- Algumas texturas possuem padding/alinhamento interno
- Não utiliza RenderWare TXD
- Estrutura básica:
  - Header
  - Palette / CLUT (quando presente)
  - Dados da imagem
  
# Final Exam
O Final Exam usa o formato .hvt (HydraVision modern), diferente do usado nos jogos Obscure clássicos. Ele armazena texturas standalone com suporte a múltiplas plataformas (PC, PS3, Xbox 360), variando principalmente em endianness, compressão e layout de memória.

## (PC) .hvt
**Features**
- Little-endian
- Textura única por arquivo
- Suporta mipmaps
- Header baseado em chunks (HEAD, DATA)
- Formatos de pixel identificados por tags ASCII (invertidas em alguns casos)
- Estrutura moderna comparada aos formatos antigos da HydraVision

**Supported pixel formats**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| BGRA                |   BGRA  | 32 bpp (linear, com alpha)               |
| BGRX                |   BGRX  | 32 bpp (alpha forçado opaco)             |
| 1TXD                |   DXT1 (BC1)  | 4 bpp (compressão sem alpha ou 1-bit alpha)                |
| 3TXD                |   DXT3 (BC2)  | 8 bpp (alpha explícito 4-bit)                |
| 5TXD                |   DXT5 (BC3)  | 8 bpp (alpha interpolado)                |

**Notes**
- Tags como 1TXD, 3TXD, 5TXD são DXT1/3/5 invertidos (armazenados ao contrário no PC)
- Dados BC (DXT) são armazenados em little-endian padrão de PC
- Não há swizzling ou tiling (diferente do Xbox 360)
- BGRX ignora o canal alpha (sempre tratado como 255)
- Estrutura usa:
  - HEAD → metadados
  - DATA → dados da textura (mip0 primeiro)
 
## (Xbox) .hvt
**Features**
- Big-endian
- Textura única por arquivo
- Suporta mipmaps
- Header baseado em chunks (HEAD, X360, DATA)
- Usa tiling (swizzle de GPU) obrigatório
- Requer byte swap (16-bit) antes do decode
- Estrutura semelhante ao PS3, mas com layout de memória diferente (tiled)
- Dados podem conter padding (alinhamento)

**Supported pixel formats**
| ID                     | Formato | Descrição                        |
|--------------------------|:------:|----------------------------------|
| DXT1 / 1TXD                |   DXT1 (BC1)  | 4 bpp (compressão sem alpha ou 1-bit alpha)               |
| DXT3 / 3TXD                |   DXT3 (BC2)  | 8 bpp (alpha explícito 4-bit)             |
| DXT5 / 5TXD                |   DXT5 (BC3)  | 8 bpp (alpha interpolado)                |
| ARGB                |   ARGB  | 32 bpp (com alpha)                |

**Notes**

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

# How to make a tool like this
To create a tool for extracting and rebuilding textures from old games, you need to determine information about the textures, such as: pixel format, endianness type, swizzling type, palette endianness, etc. To do this, you can use tools such as [ImageHeat](https://github.com/bartlomiejduda/ImageHeat), MummGGTool (MummRa's Graphic Tool) and hex editors (such as [ImHex](https://github.com/WerWolv/ImHex), for example).
