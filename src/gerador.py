import io
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src.utils import log


# ─────────────────────────────────────────────
# Constantes de layout (valores fixos do template)
# ─────────────────────────────────────────────

LARGURA = 1080
ALTURA = 1350
FUNDO = "#0D0D0D"
MARGEM = 60
LARGURA_CONTEUDO = LARGURA - MARGEM * 2  # 960px

# Cores
COR_TITULO = "#FFFFFF"
COR_SUBTITULO = "#D0D0D0"
COR_HANDLE_BG = "#1A1A1A"
COR_HANDLE_TEXT = "#FFFFFF"
COR_NAV = "#666666"
COR_CARD_BG = "#FFFFFF"
COR_CARD_TEXT = "#0D0D0D"
COR_FALLBACK_IMG = "#262626"

# Tipografia
FONTE_BOLD = "BricolageGrotesque-Bold.ttf"
FONTE_REGULAR = "BricolageGrotesque-Regular.ttf"

# Tamanhos de fonte
TITULO_CAPA_SIZE = 80
TITULO_CORPO_SIZE = 56
SUBTITULO_SIZE = 28
HANDLE_SIZE = 24
NAV_SIZE = 22
CTA_DESTAQUE_SIZE = 64

# Capa
CAPA_CATEGORIA_SIZE = 26
CAPA_ENGAJAMENTO_SIZE = 28
CAPA_LINHA_Y = 200
CAPA_LINHA_W = 120
CAPA_LINHA_H = 3
CAPA_CATEGORIA_Y = 224
CAPA_TITULO_Y = 270
CAPA_TITULO_LINE_HEIGHT = 1.15
CAPA_ESPACAMENTO_ENGAJAMENTO = 32
CAPA_OVERLAY_OPACITY = 140  # 55% de 255 ≈ 140
CAPA_SOMBRA_OFFSET = 3

# Corpo - CORREÇÃO 3: proporções fixas
TITULO_LINE_HEIGHT = 1.2
SUBTITULO_LINE_HEIGHT = 1.3
Y_TITULO_CORPO = 80
ESPACAMENTO_TITULO_SUB = 20
CORPO_IMG_Y = 607          # zona de imagem começa em 607px
CORPO_IMG_H = 623           # 1230 - 607 = 623px de imagem
CORPO_RODAPE_Y = 1230       # rodapé começa em 1230px
BORDER_RADIUS = 24

# CTA Crescitech
CTA_CARD_BG = "#1A1A1A"
CTA_CARD_ALTURA = 280
CTA_ESPACAMENTO_SUB_CARD = 48
CTA_LOGO_RAIO = 70
CTA_LOGO_BG = "#2D1B6B"
CTA_LOGO_COR = "#00D4FF"
CTA_LOGO_LETRA_SIZE = 72
CTA_NOME_SIZE = 36
CTA_DESC_SIZE = 24
CTA_DESC_COR = "#888888"
CTA_BTN_TEXT = "SEGUIR"
CTA_BTN_SIZE = 28
CTA_BTN_BG = "#FFFFFF"
CTA_BTN_COR = "#0D0D0D"
CTA_BTN_PAD_H = 16
CTA_BTN_PAD_V = 12
CTA_BTN_RADIUS = 50
CTA_BTN_MARGEM_DIR = 40

# Rodapé
HANDLE_PAD_H = 20
HANDLE_PAD_V = 10
NAV_TEXTO = "Arrasta para o lado >"
NAV_TEXTO_CTA = "Acesse nosso perfil no Instagram"


# ─────────────────────────────────────────────
# Cache de fontes
# ─────────────────────────────────────────────

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _fonte(nome: str, tamanho: int) -> ImageFont.FreeTypeFont:
    """Carrega fonte da pasta fonts/ com cache."""
    chave = (nome, tamanho)
    if chave not in _font_cache:
        caminho = Path("fonts") / nome
        _font_cache[chave] = ImageFont.truetype(str(caminho), tamanho)
    return _font_cache[chave]


# ─────────────────────────────────────────────
# Função principal
# ─────────────────────────────────────────────

def gerar_carrossel(conteudo: dict, pasta_saida: str) -> list[str]:
    """
    Recebe o conteúdo normalizado e gera todos os slides.
    Retorna lista com os caminhos dos PNGs gerados.
    """
    caminhos = []
    handle = conteudo.get("handle", "")

    for i, slide in enumerate(conteudo["slides"]):
        tipo = slide["tipo"]
        log(f"Gerando slide {i + 1}/{len(conteudo['slides'])} (tipo: {tipo})")

        if tipo == "capa":
            img = _slide_capa(slide, handle)
        elif tipo == "corpo":
            img = _slide_corpo(slide, handle)
        elif tipo == "cta":
            img = _slide_cta(slide, handle)
        else:
            log(f"Tipo de slide desconhecido: {tipo}", "WARN")
            continue

        nome_arquivo = f"slide_{i + 1:02d}_{tipo}.png"
        caminho = str(Path(pasta_saida) / nome_arquivo)
        img.save(caminho, "PNG")
        caminhos.append(caminho)
        log(f"Salvo: {caminho}")

    return caminhos


# ─────────────────────────────────────────────
# Slide: CAPA (CORREÇÃO 1 - imagem de fundo)
# ─────────────────────────────────────────────

def _slide_capa(dados: dict, handle: str) -> Image.Image:
    """
    Slide de capa com imagem de fundo:
    1. Imagem de fundo 1080x1350 (crop central)
    2. Overlay preto 55% opacidade
    3. Linha decorativa branca 120x3px
    4. Categoria em maiúsculas cinza
    5. Título Bold 80px com sombra
    6. Texto de engajamento com sombra
    7. Rodapé padrão
    """
    # 1. Imagem de fundo
    url_bg = dados.get("url_imagem")
    if url_bg:
        try:
            response = requests.get(url_bg, timeout=30)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content)).convert("RGB")
            img = _crop_central(img, LARGURA, ALTURA)
        except Exception as e:
            log(f"Erro ao baixar imagem de fundo da capa: {e}", "WARN")
            img = Image.new("RGB", (LARGURA, ALTURA), FUNDO)
    else:
        img = Image.new("RGB", (LARGURA, ALTURA), FUNDO)

    # 2. Overlay escuro 55% opacidade
    overlay = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, CAPA_OVERLAY_OPACITY))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")

    draw = ImageDraw.Draw(img)

    # 3. Linha decorativa horizontal
    draw.rectangle(
        [(MARGEM, CAPA_LINHA_Y), (MARGEM + CAPA_LINHA_W, CAPA_LINHA_Y + CAPA_LINHA_H)],
        fill=COR_TITULO,
    )

    # 4. Categoria (tema em maiúsculas, cinza)
    fonte_cat = _fonte(FONTE_REGULAR, CAPA_CATEGORIA_SIZE)
    categoria = dados.get("categoria", "")
    draw.text((MARGEM, CAPA_CATEGORIA_Y), categoria, font=fonte_cat, fill="#888888")

    # 5. Título principal (Bold 80px, max 2 linhas, com sombra)
    fonte_titulo = _fonte(FONTE_BOLD, TITULO_CAPA_SIZE)
    titulo = dados.get("titulo", "")
    linhas = _wrap_texto(titulo, fonte_titulo, LARGURA_CONTEUDO)[:2]
    line_h = int(TITULO_CAPA_SIZE * CAPA_TITULO_LINE_HEIGHT)

    y = CAPA_TITULO_Y
    for linha in linhas:
        # Sombra do texto
        draw.text((MARGEM + CAPA_SOMBRA_OFFSET, y + CAPA_SOMBRA_OFFSET),
                  linha, font=fonte_titulo, fill="#000000")
        # Texto principal
        draw.text((MARGEM, y), linha, font=fonte_titulo, fill=COR_TITULO)
        y += line_h

    # 6. Texto de engajamento (com sombra)
    y += CAPA_ESPACAMENTO_ENGAJAMENTO
    fonte_eng = _fonte(FONTE_REGULAR, CAPA_ENGAJAMENTO_SIZE)
    engajamento = dados.get("engajamento", "")
    if engajamento:
        draw.text((MARGEM + CAPA_SOMBRA_OFFSET, y + CAPA_SOMBRA_OFFSET),
                  engajamento, font=fonte_eng, fill="#000000")
        draw.text((MARGEM, y), engajamento, font=fonte_eng, fill=COR_SUBTITULO)

    # 7. Rodapé
    _desenhar_rodape(draw, handle)

    return img


# ─────────────────────────────────────────────
# Slide: CORPO (CORREÇÃO 3 - proporções fixas)
# ─────────────────────────────────────────────

def _slide_corpo(dados: dict, handle: str) -> Image.Image:
    """
    Slide intermediário com proporções fixas:
    - Zona de texto: 0 a 607px (45% superior)
    - Zona de imagem: 607px a 1230px (50%)
    - Rodapé: 1230px a 1350px (120px)
    - Título Bold 56px em y=80, max 3 linhas, margem 60px
    - Subtítulo Regular 28px, 20px abaixo, max 3 linhas, margem 60px
    - Imagem 960x623px, border-radius 24px só nos cantos superiores
    """
    img = Image.new("RGB", (LARGURA, ALTURA), FUNDO)
    draw = ImageDraw.Draw(img)

    y = Y_TITULO_CORPO

    # Título (max 3 linhas, Bold 56px)
    fonte_titulo = _fonte(FONTE_BOLD, TITULO_CORPO_SIZE)
    titulo = dados.get("titulo", "")
    linhas_titulo = _wrap_texto(titulo, fonte_titulo, LARGURA_CONTEUDO)[:3]
    line_h_titulo = int(TITULO_CORPO_SIZE * TITULO_LINE_HEIGHT)

    for linha in linhas_titulo:
        draw.text((MARGEM, y), linha, font=fonte_titulo, fill=COR_TITULO)
        y += line_h_titulo

    y += ESPACAMENTO_TITULO_SUB

    # Subtítulo (max 3 linhas, Regular 28px)
    fonte_sub = _fonte(FONTE_REGULAR, SUBTITULO_SIZE)
    subtitulo = dados.get("subtitulo", "")
    linhas_sub = _wrap_texto(subtitulo, fonte_sub, LARGURA_CONTEUDO)[:3]
    line_h_sub = int(SUBTITULO_SIZE * SUBTITULO_LINE_HEIGHT)

    for linha in linhas_sub:
        draw.text((MARGEM, y), linha, font=fonte_sub, fill=COR_SUBTITULO)
        y += line_h_sub

    # Imagem em posição fixa: y=607, largura=960, altura=623
    url = dados.get("url_imagem")
    _colar_imagem_corpo(img, url, MARGEM, CORPO_IMG_Y, LARGURA_CONTEUDO, CORPO_IMG_H, BORDER_RADIUS)

    # Rodapé
    draw = ImageDraw.Draw(img)  # recriar draw após paste
    _desenhar_rodape(draw, handle)

    return img


# ─────────────────────────────────────────────
# Slide: CTA
# ─────────────────────────────────────────────

def _slide_cta(dados: dict, handle: str) -> Image.Image:
    """
    Slide CTA Crescitech:
    - Título + subtítulo no topo
    - Card de perfil #1A1A1A com logo, nome, descrição e botão SEGUIR
    - Rodapé com texto alternativo (sem "Arrasta para o lado >")
    """
    img = Image.new("RGB", (LARGURA, ALTURA), FUNDO)
    draw = ImageDraw.Draw(img)

    y = Y_TITULO_CORPO

    # Título
    fonte_titulo = _fonte(FONTE_BOLD, TITULO_CORPO_SIZE)
    titulo = dados.get("titulo", "")
    linhas_titulo = _wrap_texto(titulo, fonte_titulo, LARGURA_CONTEUDO)[:3]
    line_h_titulo = int(TITULO_CORPO_SIZE * TITULO_LINE_HEIGHT)

    for linha in linhas_titulo:
        draw.text((MARGEM, y), linha, font=fonte_titulo, fill=COR_TITULO)
        y += line_h_titulo

    y += ESPACAMENTO_TITULO_SUB

    # Subtítulo
    fonte_sub = _fonte(FONTE_REGULAR, SUBTITULO_SIZE)
    subtitulo = dados.get("subtitulo", "")
    linhas_sub = _wrap_texto(subtitulo, fonte_sub, LARGURA_CONTEUDO)[:3]
    line_h_sub = int(SUBTITULO_SIZE * SUBTITULO_LINE_HEIGHT)

    for linha in linhas_sub:
        draw.text((MARGEM, y), linha, font=fonte_sub, fill=COR_SUBTITULO)
        y += line_h_sub

    y += CTA_ESPACAMENTO_SUB_CARD

    # Card de perfil
    card_x = MARGEM
    card_y = y
    card_w = LARGURA_CONTEUDO
    card_h = CTA_CARD_ALTURA

    draw.rounded_rectangle(
        [(card_x, card_y), (card_x + card_w, card_y + card_h)],
        radius=BORDER_RADIUS,
        fill=CTA_CARD_BG,
    )

    # Logo: círculo roxo com "C" em ciano
    logo_cx = card_x + 60 + CTA_LOGO_RAIO  # centro X do círculo
    logo_cy = card_y + card_h // 2          # centro Y do círculo
    draw.ellipse(
        [(logo_cx - CTA_LOGO_RAIO, logo_cy - CTA_LOGO_RAIO),
         (logo_cx + CTA_LOGO_RAIO, logo_cy + CTA_LOGO_RAIO)],
        fill=CTA_LOGO_BG,
    )
    fonte_logo = _fonte(FONTE_BOLD, CTA_LOGO_LETRA_SIZE)
    bbox_c = fonte_logo.getbbox("C")
    c_w = bbox_c[2] - bbox_c[0]
    c_h = bbox_c[3] - bbox_c[1]
    draw.text(
        (logo_cx - c_w // 2, logo_cy - c_h // 2 - bbox_c[1]),
        "C", font=fonte_logo, fill=CTA_LOGO_COR,
    )

    # Nome "@crescitech"
    texto_x = card_x + 60 + CTA_LOGO_RAIO * 2 + 40  # após o logo + gap
    fonte_nome = _fonte(FONTE_BOLD, CTA_NOME_SIZE)
    nome = "@crescitech"
    bbox_nome = fonte_nome.getbbox(nome)
    nome_h = bbox_nome[3] - bbox_nome[1]

    # Posicionar nome e descrição centrados verticalmente no card
    fonte_desc = _fonte(FONTE_REGULAR, CTA_DESC_SIZE)
    descricao = "Consultoria em Inteligencia Artificial"
    bbox_desc = fonte_desc.getbbox(descricao)
    desc_h = bbox_desc[3] - bbox_desc[1]

    bloco_texto_h = nome_h + 12 + desc_h  # 12px gap entre nome e desc
    texto_y_inicio = card_y + (card_h - bloco_texto_h) // 2

    draw.text(
        (texto_x, texto_y_inicio - bbox_nome[1]),
        nome, font=fonte_nome, fill=COR_TITULO,
    )
    draw.text(
        (texto_x, texto_y_inicio + nome_h + 12 - bbox_desc[1]),
        descricao, font=fonte_desc, fill=CTA_DESC_COR,
    )

    # Botão "SEGUIR"
    fonte_btn = _fonte(FONTE_BOLD, CTA_BTN_SIZE)
    bbox_btn = fonte_btn.getbbox(CTA_BTN_TEXT)
    btn_text_w = bbox_btn[2] - bbox_btn[0]
    btn_text_h = bbox_btn[3] - bbox_btn[1]
    btn_w = btn_text_w + CTA_BTN_PAD_H * 2
    btn_h = btn_text_h + CTA_BTN_PAD_V * 2

    btn_x = card_x + card_w - CTA_BTN_MARGEM_DIR - btn_w
    btn_y = card_y + (card_h - btn_h) // 2

    draw.rounded_rectangle(
        [(btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h)],
        radius=CTA_BTN_RADIUS,
        fill=CTA_BTN_BG,
    )
    draw.text(
        (btn_x + CTA_BTN_PAD_H, btn_y + CTA_BTN_PAD_V - bbox_btn[1]),
        CTA_BTN_TEXT, font=fonte_btn, fill=CTA_BTN_COR,
    )

    # Rodapé (texto alternativo para CTA)
    _desenhar_rodape(draw, handle, nav_texto=NAV_TEXTO_CTA)

    return img


# ─────────────────────────────────────────────
# Rodapé (compartilhado por todos os slides)
# ─────────────────────────────────────────────

def _desenhar_rodape(draw: ImageDraw.ImageDraw, handle: str,
                     nav_texto: str | None = None) -> None:
    """
    Rodapé fixo em todos os slides:
    - Handle em pílula arredondada: x=60, alinhado ao fundo
    - Texto de navegação: alinhado à direita, mesma altura
    - Posição Y: 1350 - 60 - altura_pilula
    """
    if nav_texto is None:
        nav_texto = NAV_TEXTO

    fonte_handle = _fonte(FONTE_REGULAR, HANDLE_SIZE)
    fonte_nav = _fonte(FONTE_REGULAR, NAV_SIZE)

    # Medir handle
    bbox_h = fonte_handle.getbbox(handle)
    texto_h_w = bbox_h[2] - bbox_h[0]
    texto_h_h = bbox_h[3] - bbox_h[1]

    pill_w = texto_h_w + HANDLE_PAD_H * 2
    pill_h = texto_h_h + HANDLE_PAD_V * 2
    pill_radius = pill_h // 2  # pílula totalmente arredondada

    pill_x = MARGEM
    pill_y = ALTURA - MARGEM - pill_h

    # Pílula do handle
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=pill_radius,
        fill=COR_HANDLE_BG,
    )

    # Texto do handle centralizado na pílula
    text_x = pill_x + HANDLE_PAD_H
    text_y = pill_y + HANDLE_PAD_V - bbox_h[1]  # compensar ascent
    draw.text((text_x, text_y), handle, font=fonte_handle, fill=COR_HANDLE_TEXT)

    # Navegação (direita, mesma altura vertical que o handle)
    bbox_nav = fonte_nav.getbbox(nav_texto)
    nav_w = bbox_nav[2] - bbox_nav[0]
    nav_h = bbox_nav[3] - bbox_nav[1]

    x_nav = LARGURA - MARGEM - nav_w
    # Centralizar verticalmente com a pílula
    y_nav = pill_y + (pill_h - nav_h) // 2 - bbox_nav[1]
    draw.text((x_nav, y_nav), nav_texto, font=fonte_nav, fill=COR_NAV)


# ─────────────────────────────────────────────
# Imagem arredondada para slides corpo
# (CORREÇÃO 3: border-radius apenas nos cantos superiores)
# ─────────────────────────────────────────────

def _colar_imagem_corpo(img: Image.Image, url: str | None,
                        x: int, y: int, w: int, h: int, raio: int) -> None:
    """
    Baixa a imagem da URL, redimensiona para wxh com crop central,
    aplica máscara com border-radius apenas nos cantos superiores
    (inferior toca o rodapé sem radius).
    Fallback: retângulo #262626 se a imagem não carregar.
    """
    foto = None

    if url:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            foto = Image.open(io.BytesIO(response.content)).convert("RGB")
            foto = _crop_central(foto, w, h)
        except Exception as e:
            log(f"Erro ao baixar imagem: {e}", "WARN")
            foto = None

    if foto is None:
        foto = Image.new("RGB", (w, h), COR_FALLBACK_IMG)

    # Máscara com border-radius apenas nos cantos superiores
    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)
    # Desenhar retângulo arredondado completo
    mask_draw.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=raio, fill=255)
    # Preencher cantos inferiores (sem radius) - sobrescrever com retângulo
    mask_draw.rectangle([(0, h - raio), (w - 1, h - 1)], fill=255)

    img.paste(foto, (x, y), mask)


def _crop_central(foto: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Redimensiona e faz crop central para encaixar exatamente no target."""
    orig_w, orig_h = foto.size
    target_ratio = target_w / target_h
    orig_ratio = orig_w / orig_h

    if orig_ratio > target_ratio:
        # Imagem mais larga: ajustar pela altura, cortar largura
        new_h = target_h
        new_w = int(orig_w * (target_h / orig_h))
    else:
        # Imagem mais alta: ajustar pela largura, cortar altura
        new_w = target_w
        new_h = int(orig_h * (target_w / orig_w))

    foto = foto.resize((new_w, new_h), Image.LANCZOS)

    # Crop central
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return foto.crop((left, top, left + target_w, top + target_h))


# ─────────────────────────────────────────────
# Quebra de texto
# ─────────────────────────────────────────────

def _wrap_texto(texto: str, fonte: ImageFont.FreeTypeFont, largura_max: int) -> list[str]:
    """
    Quebra o texto em linhas respeitando a largura máxima em pixels.
    Usa getbbox para medir a largura real de cada combinação.
    """
    if not texto:
        return []

    palavras = texto.split()
    linhas = []
    linha_atual = ""

    for palavra in palavras:
        teste = f"{linha_atual} {palavra}".strip()
        bbox = fonte.getbbox(teste)
        largura_teste = bbox[2] - bbox[0]

        if largura_teste <= largura_max:
            linha_atual = teste
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = palavra

    if linha_atual:
        linhas.append(linha_atual)

    return linhas
