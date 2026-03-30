import io
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src.utils import log


# ─────────────────────────────────────────────
# Constantes de layout — medidas exatas do template
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
COR_FALLBACK_IMG = "#1A1A1A"

# Tipografia
FONTE_BOLD = "BricolageGrotesque-Bold.ttf"
FONTE_REGULAR = "BricolageGrotesque-Regular.ttf"

# ── Capa ──
CAPA_TITULO_SIZE = 80
CAPA_CATEGORIA_SIZE = 26
CAPA_ENGAJAMENTO_SIZE = 28
CAPA_OVERLAY = (0, 0, 0, 160)        # RGBA preto 63% opacidade
CAPA_SOMBRA = 3                       # offset sombra em px
CAPA_LINHA_Y = 180
CAPA_LINHA_W = 120
CAPA_LINHA_H = 3
CAPA_CATEGORIA_Y = 194
CAPA_TITULO_Y = 240
CAPA_TITULO_LH = 1.15
CAPA_ENG_GAP = 28                     # gap entre última linha do título e engajamento

# ── Corpo ──
CORPO_TITULO_SIZE = 56
CORPO_TEXTO_SIZE = 28
CORPO_TITULO_Y = 60
CORPO_TITULO_LH = 1.2
CORPO_TEXTO_LH = 1.4                  # parágrafo precisa de mais espaço
CORPO_GAP_TIT_TEXTO = 20
CORPO_TEXTO_LIMITE_Y = 248            # 20px antes do card (268 - 20)
CORPO_IMG_Y = 268                     # posição fixa do card/imagem
CORPO_IMG_BOTTOM = 1105               # fim do card/imagem
CORPO_IMG_H = CORPO_IMG_BOTTOM - CORPO_IMG_Y  # 837px
BORDER_RADIUS = 24

# ── CTA ──
CTA_TITULO_SIZE = 56
CTA_SUBTITULO_SIZE = 28
CTA_TITULO_Y = 60
CTA_TITULO_LH = 1.2
CTA_SUBTITULO_LH = 1.3
CTA_GAP_TIT_SUB = 20
CTA_CARD_Y = 268
CTA_CARD_H = 280
CTA_CARD_BG = "#1A1A1A"
CTA_LOGO_RAIO = 55
CTA_LOGO_BG = "#2D1B6B"
CTA_LOGO_COR = "#00D4FF"
CTA_LOGO_LETRA_SIZE = 60
CTA_LOGO_X_OFFSET = 100               # centro do logo, offset do início do card
CTA_TEXTO_X_OFFSET = 160              # início do texto, offset do início do card
CTA_NOME_SIZE = 34
CTA_DESC_SIZE = 22
CTA_DESC_COR = "#888888"
CTA_DESC_GAP = 8
CTA_BTN_TEXT = "SEGUIR"
CTA_BTN_SIZE = 26
CTA_BTN_BG = "#FFFFFF"
CTA_BTN_COR = "#0D0D0D"
CTA_BTN_PAD_H = 14
CTA_BTN_PAD_V = 10
CTA_BTN_RADIUS = 50
CTA_BTN_MARGEM_DIR = 40

# ── Rodapé ──
RODAPE_Y = 1256
HANDLE_SIZE = 24
NAV_SIZE = 22
HANDLE_PAD_H = 20
HANDLE_PAD_V = 10
NAV_TEXTO = "Arrasta para o lado >"
NAV_TEXTO_CTA = "Acesse nosso perfil no Instagram"


# ─────────────────────────────────────────────
# Cache de fontes
# ─────────────────────────────────────────────

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _fonte(nome: str, tamanho: int) -> ImageFont.FreeTypeFont:
    chave = (nome, tamanho)
    if chave not in _font_cache:
        caminho = Path("fonts") / nome
        _font_cache[chave] = ImageFont.truetype(str(caminho), tamanho)
    return _font_cache[chave]


# ─────────────────────────────────────────────
# Função principal
# ─────────────────────────────────────────────

def gerar_carrossel(conteudo: dict, pasta_saida: str) -> list[str]:
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
# Slide: CAPA
# ─────────────────────────────────────────────

def _slide_capa(dados: dict, handle: str) -> Image.Image:
    # Imagem de fundo cobrindo 100% do canvas
    url_bg = dados.get("url_imagem")
    if url_bg:
        try:
            resp = requests.get(url_bg, timeout=30)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            img = _crop_central(img, LARGURA, ALTURA)
        except Exception as e:
            log(f"Erro ao baixar imagem de fundo da capa: {e}", "WARN")
            img = Image.new("RGB", (LARGURA, ALTURA), FUNDO)
    else:
        img = Image.new("RGB", (LARGURA, ALTURA), FUNDO)

    # Overlay escuro RGBA(0,0,0,160)
    overlay = Image.new("RGBA", (LARGURA, ALTURA), CAPA_OVERLAY)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)

    # Linha decorativa branca
    draw.rectangle(
        [(MARGEM, CAPA_LINHA_Y), (MARGEM + CAPA_LINHA_W, CAPA_LINHA_Y + CAPA_LINHA_H)],
        fill=COR_TITULO,
    )

    # Categoria
    fonte_cat = _fonte(FONTE_REGULAR, CAPA_CATEGORIA_SIZE)
    draw.text((MARGEM, CAPA_CATEGORIA_Y), dados.get("categoria", ""), font=fonte_cat, fill="#888888")

    # Título Bold 80px com sombra, max 2 linhas
    fonte_tit = _fonte(FONTE_BOLD, CAPA_TITULO_SIZE)
    linhas = _wrap_texto(dados.get("titulo", ""), fonte_tit, LARGURA_CONTEUDO)[:2]
    lh = int(CAPA_TITULO_SIZE * CAPA_TITULO_LH)

    y = CAPA_TITULO_Y
    for linha in linhas:
        draw.text((MARGEM + CAPA_SOMBRA, y + CAPA_SOMBRA), linha, font=fonte_tit, fill="#000000")
        draw.text((MARGEM, y), linha, font=fonte_tit, fill=COR_TITULO)
        y += lh

    # Engajamento com sombra, 28px abaixo do título
    y += CAPA_ENG_GAP
    eng = dados.get("engajamento", "")
    if eng:
        fonte_eng = _fonte(FONTE_REGULAR, CAPA_ENGAJAMENTO_SIZE)
        draw.text((MARGEM + CAPA_SOMBRA, y + CAPA_SOMBRA), eng, font=fonte_eng, fill="#000000")
        draw.text((MARGEM, y), eng, font=fonte_eng, fill=COR_SUBTITULO)

    # Rodapé
    _desenhar_rodape(draw, handle)
    return img


# ─────────────────────────────────────────────
# Slide: CORPO
# ─────────────────────────────────────────────

def _slide_corpo(dados: dict, handle: str) -> Image.Image:
    img = Image.new("RGB", (LARGURA, ALTURA), FUNDO)
    draw = ImageDraw.Draw(img)

    # Título Bold 56px, y=60, max 3 linhas
    fonte_tit = _fonte(FONTE_BOLD, CORPO_TITULO_SIZE)
    linhas_tit = _wrap_texto(dados.get("titulo", ""), fonte_tit, LARGURA_CONTEUDO)[:3]
    lh_tit = int(CORPO_TITULO_SIZE * CORPO_TITULO_LH)

    y = CORPO_TITULO_Y
    for linha in linhas_tit:
        draw.text((MARGEM, y), linha, font=fonte_tit, fill=COR_TITULO)
        y += lh_tit

    # Bloco de texto narrativo: Regular 28px, LH 1.4, sem limite de linhas
    # Ocupa o espaço que precisar até y=248 (20px antes do card em y=268)
    y += CORPO_GAP_TIT_TEXTO
    fonte_txt = _fonte(FONTE_REGULAR, CORPO_TEXTO_SIZE)
    texto = dados.get("texto", "") or dados.get("subtitulo", "")
    linhas_txt = _wrap_texto(texto, fonte_txt, LARGURA_CONTEUDO)
    lh_txt = int(CORPO_TEXTO_SIZE * CORPO_TEXTO_LH)

    for i, linha in enumerate(linhas_txt):
        prox_y = y + lh_txt
        if prox_y > CORPO_TEXTO_LIMITE_Y:
            # Última linha que cabe: cortar com "..."
            linha_cortada = linha
            while fonte_txt.getbbox(linha_cortada + "...")[2] - fonte_txt.getbbox(linha_cortada + "...")[0] > LARGURA_CONTEUDO:
                palavras = linha_cortada.rsplit(" ", 1)
                if len(palavras) <= 1:
                    break
                linha_cortada = palavras[0]
            draw.text((MARGEM, y), linha_cortada + "...", font=fonte_txt, fill=COR_SUBTITULO)
            break
        draw.text((MARGEM, y), linha, font=fonte_txt, fill=COR_SUBTITULO)
        y += lh_txt

    # Card/imagem arredondado: y=268 fixo, 960x837, border-radius 24px todos os cantos
    url = dados.get("url_imagem")
    _colar_imagem_arredondada(img, url, MARGEM, CORPO_IMG_Y, LARGURA_CONTEUDO, CORPO_IMG_H, BORDER_RADIUS)

    # Rodapé
    draw = ImageDraw.Draw(img)
    _desenhar_rodape(draw, handle)
    return img


# ─────────────────────────────────────────────
# Slide: CTA
# ─────────────────────────────────────────────

def _slide_cta(dados: dict, handle: str) -> Image.Image:
    img = Image.new("RGB", (LARGURA, ALTURA), FUNDO)
    draw = ImageDraw.Draw(img)

    # Título Bold 56px, y=60, max 2 linhas
    fonte_tit = _fonte(FONTE_BOLD, CTA_TITULO_SIZE)
    linhas_tit = _wrap_texto(dados.get("titulo", ""), fonte_tit, LARGURA_CONTEUDO)[:2]
    lh_tit = int(CTA_TITULO_SIZE * CTA_TITULO_LH)

    y = CTA_TITULO_Y
    for linha in linhas_tit:
        draw.text((MARGEM, y), linha, font=fonte_tit, fill=COR_TITULO)
        y += lh_tit

    # Subtítulo Regular 28px, 20px abaixo, max 2 linhas
    y += CTA_GAP_TIT_SUB
    fonte_sub = _fonte(FONTE_REGULAR, CTA_SUBTITULO_SIZE)
    linhas_sub = _wrap_texto(dados.get("subtitulo", ""), fonte_sub, LARGURA_CONTEUDO)[:2]
    lh_sub = int(CTA_SUBTITULO_SIZE * CTA_SUBTITULO_LH)

    for linha in linhas_sub:
        draw.text((MARGEM, y), linha, font=fonte_sub, fill=COR_SUBTITULO)
        y += lh_sub

    # Card de perfil Crescitech em y=268 fixo
    card_x = MARGEM
    card_y = CTA_CARD_Y
    card_w = LARGURA_CONTEUDO
    card_h = CTA_CARD_H

    draw.rounded_rectangle(
        [(card_x, card_y), (card_x + card_w, card_y + card_h)],
        radius=BORDER_RADIUS,
        fill=CTA_CARD_BG,
    )

    # Logo: círculo roxo com "C" em ciano
    logo_cx = card_x + CTA_LOGO_X_OFFSET
    logo_cy = card_y + card_h // 2
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

    # Nome e descrição
    texto_x = card_x + CTA_TEXTO_X_OFFSET
    fonte_nome = _fonte(FONTE_BOLD, CTA_NOME_SIZE)
    fonte_desc = _fonte(FONTE_REGULAR, CTA_DESC_SIZE)

    nome = "@crescitech"
    descricao = "Consultoria em Inteligencia Artificial"

    bbox_nome = fonte_nome.getbbox(nome)
    nome_h = bbox_nome[3] - bbox_nome[1]
    bbox_desc = fonte_desc.getbbox(descricao)
    desc_h = bbox_desc[3] - bbox_desc[1]

    bloco_h = nome_h + CTA_DESC_GAP + desc_h
    ty = card_y + (card_h - bloco_h) // 2

    draw.text((texto_x, ty - bbox_nome[1]), nome, font=fonte_nome, fill=COR_TITULO)
    draw.text((texto_x, ty + nome_h + CTA_DESC_GAP - bbox_desc[1]), descricao, font=fonte_desc, fill=CTA_DESC_COR)

    # Botão SEGUIR
    fonte_btn = _fonte(FONTE_BOLD, CTA_BTN_SIZE)
    bbox_btn = fonte_btn.getbbox(CTA_BTN_TEXT)
    btn_tw = bbox_btn[2] - bbox_btn[0]
    btn_th = bbox_btn[3] - bbox_btn[1]
    btn_w = btn_tw + CTA_BTN_PAD_H * 2
    btn_h = btn_th + CTA_BTN_PAD_V * 2
    btn_x = card_x + card_w - CTA_BTN_MARGEM_DIR - btn_w
    btn_y = card_y + (card_h - btn_h) // 2

    draw.rounded_rectangle(
        [(btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h)],
        radius=CTA_BTN_RADIUS, fill=CTA_BTN_BG,
    )
    draw.text(
        (btn_x + CTA_BTN_PAD_H, btn_y + CTA_BTN_PAD_V - bbox_btn[1]),
        CTA_BTN_TEXT, font=fonte_btn, fill=CTA_BTN_COR,
    )

    # Rodapé CTA
    _desenhar_rodape(draw, handle, nav_texto=NAV_TEXTO_CTA)
    return img


# ─────────────────────────────────────────────
# Rodapé — posição fixa em y=1256
# ─────────────────────────────────────────────

def _desenhar_rodape(draw: ImageDraw.ImageDraw, handle: str,
                     nav_texto: str | None = None) -> None:
    if nav_texto is None:
        nav_texto = NAV_TEXTO

    fonte_handle = _fonte(FONTE_REGULAR, HANDLE_SIZE)
    fonte_nav = _fonte(FONTE_REGULAR, NAV_SIZE)

    # Handle em pílula
    bbox_h = fonte_handle.getbbox(handle)
    th_w = bbox_h[2] - bbox_h[0]
    th_h = bbox_h[3] - bbox_h[1]
    pill_w = th_w + HANDLE_PAD_H * 2
    pill_h = th_h + HANDLE_PAD_V * 2
    pill_r = pill_h // 2

    pill_x = MARGEM
    pill_y = RODAPE_Y

    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=pill_r, fill=COR_HANDLE_BG,
    )
    draw.text(
        (pill_x + HANDLE_PAD_H, pill_y + HANDLE_PAD_V - bbox_h[1]),
        handle, font=fonte_handle, fill=COR_HANDLE_TEXT,
    )

    # Navegação à direita, centralizada verticalmente com pílula
    bbox_nav = fonte_nav.getbbox(nav_texto)
    nav_w = bbox_nav[2] - bbox_nav[0]
    nav_h = bbox_nav[3] - bbox_nav[1]
    x_nav = LARGURA - MARGEM - nav_w
    y_nav = pill_y + (pill_h - nav_h) // 2 - bbox_nav[1]
    draw.text((x_nav, y_nav), nav_texto, font=fonte_nav, fill=COR_NAV)


# ─────────────────────────────────────────────
# Imagem arredondada — border-radius 24px todos os cantos
# ─────────────────────────────────────────────

def _colar_imagem_arredondada(img: Image.Image, url: str | None,
                               x: int, y: int, w: int, h: int, raio: int) -> None:
    foto = None
    if url:
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            foto = Image.open(io.BytesIO(resp.content)).convert("RGB")
            foto = _crop_central(foto, w, h)
        except Exception as e:
            log(f"Erro ao baixar imagem: {e}", "WARN")
            foto = None

    if foto is None:
        foto = Image.new("RGB", (w, h), COR_FALLBACK_IMG)

    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=raio, fill=255)
    img.paste(foto, (x, y), mask)


def _crop_central(foto: Image.Image, tw: int, th: int) -> Image.Image:
    ow, oh = foto.size
    tr = tw / th
    orr = ow / oh
    if orr > tr:
        nw = int(ow * (th / oh))
        foto = foto.resize((nw, th), Image.LANCZOS)
    else:
        nh = int(oh * (tw / ow))
        foto = foto.resize((tw, nh), Image.LANCZOS)
    nw, nh = foto.size
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return foto.crop((left, top, left + tw, top + th))


# ─────────────────────────────────────────────
# Quebra de texto
# ─────────────────────────────────────────────

def _wrap_texto(texto: str, fonte: ImageFont.FreeTypeFont, largura_max: int) -> list[str]:
    if not texto:
        return []
    palavras = texto.split()
    linhas = []
    atual = ""
    for p in palavras:
        teste = f"{atual} {p}".strip()
        if fonte.getbbox(teste)[2] - fonte.getbbox(teste)[0] <= largura_max:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas
