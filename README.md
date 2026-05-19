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
or
```bash
./obscure_texture_tool.exe extract TextureName.Format(, dic, .dip, .hvt, .hvi ou .xbr)
```

**Rebuild:**
```bash
obscure_texture_tool.exe rebuild TextureName.Format TextureFile/
```
or
```bash
./obscure_texture_tool.exe rebuild TextureName.Format TextureFile/
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
(instead of p + 28)
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
| Tag                     | Format | 
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
Obscure 1 uses .dip files, and Obscure 2 uses .dic files (texture dictionaries). Both store multiple textures with mipmaps, but they differ mainly in endianness and color channel order.

### .dic
**Features**
- Big-endian
- Pode conter múltiplas texturas
- Suporta mipmaps
- Strings em Shift-JIS
- Formato semelhante ao usado em ferramentas como TexDict

**Supported pixel formats**
| ID                     | Format | Description                        |
|--------------------------|:------:|----------------------------------|
| 21                |   R8G8B8A8  | 32 bpp (RGBA)               |
| 23                |   R5G6B5  | 16 bpp (without alpha)             |
| 25                |   R5G5B5A1  | 16 bpp (1-bit alpha)                |

## .dip
**Features**
- Little-endian
- Structure very similar to .dic
- ASCII strings
- Used specifically in Obscure 1 (PC)
- Based on scripts such as fmt_dip.py (Noesis)

**Supported pixel formats**
| ID                     | Format | Description                        |
|--------------------------|:------:|----------------------------------|
| 21                |   B8G8R8A8  | 32 bpp (BGRA)               |
| 23                |   B5G6R5  | 16 bpp             |
| 25                |   B5G5R5A1  | 16 bpp (1-bit alpha)                |

## (Xbox)
The ObsCure 1 version for the Classic Xbox uses .xbr files as texture dictionaries.
This format is based directly on the NV2A GPU (derived from NVIDIA) and closely follows the Direct3D standards of the time. The .xbr format is a texture dictionary used to store multiple textures in a single file.

### .xbr
**Features**
- Little-endian
- May contain multiple textures
- Supports mipmaps
- ASCII strings
- Based on the NV2A format (Direct3D-like)
- Uses Morton swizzling (Z-order) for SZ_* textures
- Structure consisting of descriptors + name table + pixel block

**Supported pixel formats**
| ID                     | Format | Description                        |
|--------------------------|:------:|----------------------------------|
| 0x05                |   SZ_R5G6B5  | 16 bpp (RGB, swizzled)               |
| 0x02                |   SZ_A1R5G5B5  | 16 bpp (1-bit alpha, swizzled)             |
| 0x06                |   SZ_A8R8G8B8  | 32 bpp (RGBA, swizzled)                |
| 0x07                |   SZ_X8R8G8B8  | 32 bpp (RGB, swizzled)                |
| 0x11                |   LU_R5G6B5  | 16 bpp (linear)                |
| 0x12                |   LU_A8R8G8B8  | 32 bpp (linear)                |
| 0x13                |   LU_X8R8G8B8  | 32 bpp (linear)                |

**Unsupported formats (common)**
| ID                     | Format | Description                        |
|--------------------------|:------:|----------------------------------|
| 0x0C                |   DXT1  | S3TC compression               |
| 0x0E                |   DXT3  | Alpha compression             |
| 0x0F                |   DXT5  | Advanced compression                |

**Note:**
- Unlike the PS2, it does not use palettes (CLUT)
- Closer to modern APIs (Direct3D)

## (PS2) 
### .dic
**Features**
- Little-endian
- Based on RenderWare TXD
- Chunk-based structure (RW_TEXTURE_DICTIONARY, RW_TEXTURE_NATIVE, RW_STRUCT, RW_STRING)
- Multiple textures per file
- Indexed textures use PS2 swizzling (CSM1)
- Some textures use RGB5551 palette, others RGBA8888
- RGBA8888 alpha uses PS2 range (0–128)

**Supported pixel formats**
| ID                     | Format | Description                        |
|--------------------------|:------:|----------------------------------|
| 4                |   PAL4  | 4 bpp indexed (swizzled)               |
| 8                |   PAL8  | 8 bpp indexed (swizzled)             |
| 16                |   RGB5551  | 16 bpp linear                |
| 32                |   RGBA8888  | 32 bpp linear                |

**Notes**
- Swizzling follows the PS2 VRAM layout
- PAL8 uses CLUT remapping (CSM1)
- PAL4 does not use palette remapping
- Palettes can be in:
  - RGB5551
  - RGBA8888
- RGBA8888 alpha must be multiplied by 2 when decoding
- When reimporting RGBA8888:
  - alpha must be converted back to the 0–128 range
- Typical structure:
  - RW_TEXTURE_DICTIONARY
    - RW_TEXTURE_NATIVE
      - RW_STRING (name)
      - RW_STRUCT (actual texture data)

### .hvi
**Features**
- Little-endian
- Single texture per file
- Simple, linear structure
- Indexed payload is already linearized (no swizzling)
- Palette stored in BGRA8888
- Alpha often uses the reduced PS2 range

**Supported pixel formats**
| ID                     | Format | Description                        |
|--------------------------|:------:|----------------------------------|
| 8                |   PAL8  | 8 bpp indexed               |
| BGRA8888                |   Palette  | CLUT BGRA8888             |

**Notes**
- Indexed data does not use swizzling
- Palette uses BGRA order
- Some palettes use reduced alpha:
  - typically up to 0x80 or 0x90
- When decoding:
  - alpha may need to be multiplied by 2 in some files
- Typical structure:
  - Header
  - Palette BGRA8888
  - Indexed payload linear

## (PSP) .dic
**Features**
- Little-endian
- Multiple textures per file
- Simple sequential structure (no RenderWare chunks)
- Indexed textures use PSP block swizzling
- Palettes / CLUT stored in RGBA8888
- Fixed 4-byte padding between palette and image
- Some textures use direct RGBA8888 (no palette)

**Supported pixel formats**
| ID                     | Format | Description                        |
|--------------------------|:------:|----------------------------------|
| GU_PSM_T4                |   PAL4  | 4 bpp indexed (swizzled)  |
| GU_PSM_T8                |   PAL8  | 8 bpp indexed (swizzled)  |
| 32               |   RGBA8888  | 32 bpp linear  |

**Notes**
- Indexed textures use RGBA8888 CLUT
- Indexed payload is stored in PSP swizzled order
- Swizzle uses 16×8 byte blocks
- There is 4-byte padding after the palette, even when palette_size = 0
- Direct RGBA8888 textures do not use swizzling
- Does not use RenderWare TXD (unlike PS2)
- Typical structure:
  - Texture header
  - Palette / CLUT
  - Padding (4 bytes)
  - Image data

## (PSP) .hvt
**Features**
- Little-endian
- Single texture per file
- Simple structure without RenderWare containers
- Image data stored in PSP swizzled format
- Some files use CLUT / palettes
- Compatible with ObsCure Final Exam PSP interface and HUD textures
- Compact header containing dimensions and pixel format

**Supported pixel formats**
| ID                     | Format | Description                        |
|--------------------------|:------:|----------------------------------|
| GU_PSM_T4                | PAL4 | 4 bpp indexed (swizzled) |
| GU_PSM_T8                | PAL8 | 8 bpp indexed (swizzled) |
| GU_PSM_8888              | RGBA8888 | 32 bpp linear |

**Notes**
- Indexed textures use RGBA8888 palettes / CLUT
- Indexed payload uses PSP standard swizzle
- PSP swizzle uses 16×8 byte blocks
- RGBA8888 textures are stored linearly
- Some textures include internal padding / alignment
- Does not use RenderWare TXD
- Typical structure:
  - Header
  - Palette / CLUT (quando presente)
  - Image data
  
# Final Exam
The Final Exam uses the .hvt format (HydraVision modern), which is different from the one used in the classic Obscure games. It stores standalone textures with multi-platform support (PC, PS3, Xbox 360), varying mainly in endianness, compression, and memory layout.

## (PC) .hvt
**Features**
- Little-endian
- Single texture per file
- Supports mipmaps
- Header structured in chunks (HEAD, DATA)
- Pixel formats identified by ASCII tags (sometimes inverted)
- Modern structure compared to older HydraVision formats

**Supported pixel formats**
| ID                     | Format | Description                        |
|--------------------------|:------:|----------------------------------|
| BGRA                |   BGRA  | 32 bpp (linear, with alpha)               |
| BGRX                |   BGRX  | 32 bpp (alpha forced opaque)             |
| 1TXD                |   DXT1 (BC1)  | 4 bpp (compression without alpha or 1-bit alpha)                |
| 3TXD                |   DXT3 (BC2)  | 8 bpp (explicit 4-bit alpha)                |
| 5TXD                |   DXT5 (BC3)  | 8 bpp (interpolated alpha)                |

**Notes**
- Tags like 1TXD, 3TXD, 5TXD correspond to DXT1/3/5 but stored reversed (little-endian on PC)
- BC (DXT) data is stored in standard PC little-endian
- No swizzling or tiling (unlike Xbox 360)
- BGRX ignores the alpha channel (always treated as 255)
- Structure layout:
  - HEAD → metadata
  - DATA → texture data (mip0 first)
 
## (Xbox) .hvt
**Features**
- Big-endian
- Single texture per file
- Supports mipmaps
- Header based on chunks (HEAD, X360, DATA)
- Uses GPU tiling (swizzle) mandatory
- Requires 16-bit byte swap before decoding
- Layout similar to PS3, but memory is tiled differently
- Data may contain padding/alignment

**Supported pixel formats**
| ID                     | Format | Description                        |
|--------------------------|:------:|----------------------------------|
| DXT1 / 1TXD                |   DXT1 (BC1)  | 4 bpp (compression without alpha or 1-bit alpha)               |
| DXT3 / 3TXD                |   DXT3 (BC2)  | 8 bpp (explicit 4-bit alpha)             |
| DXT5 / 5TXD                |   DXT5 (BC3)  | 8 bpp (interpolated alpha)                |
| ARGB                |   ARGB  | 32 bpp (with alpha)                |

**Notes**

**Different from PC:**
- ✔ PC = linear data
- ❗ X360 = tiled (swizzled) data
  
**Textures need to go through:**
- unswizzle (GPU memory reordering)
- byte swap (endianness)
  
**Mandatory alignment:**
- BC (DXT): multiples of 128 pixels
- ARGB: multiples of 32 pixels
  
**After decoding, you must:**
- remove padding (crop) to original size
  
**BC data uses standard DXT blocks, but:**
- ❗ not stored in linear order
**Some files may contain**
- extra bytes after mip0
  
**Internal structure:**
- HEAD → metadata
- X360 → GPU configuration (tiling)
- DATA → texture data
  
**Tags may appear as:**
- DXT1 / DXT5 (standard)
- 1TXD / 5TXD (variant)

# How to make a tool like this
To create a tool for extracting and rebuilding textures from old games, you need to determine information about the textures, such as: pixel format, endianness type, swizzling type, palette endianness, etc. To do this, you can use tools such as [ImageHeat](https://github.com/bartlomiejduda/ImageHeat), MummGGTool (MummRa's Graphic Tool) and hex editors (such as [ImHex](https://github.com/WerWolv/ImHex), for example).
