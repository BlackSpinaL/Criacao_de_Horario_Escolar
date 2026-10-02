"""Geração de QR Codes para links do sistema."""
from io import BytesIO
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image, ImageDraw, ImageFont


BASE_URL = "https://sistemadecriacaodehorarioescolar.streamlit.app"

# Cores padrão (azul do sistema)
AZUL_ESCURO = (31, 78, 120)
AZUL_CLARO = (214, 234, 248)


def gerar_qr_bytes(texto, com_cor=True):
    """Gera um QR Code simples em bytes (PNG)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(texto)
    qr.make(fit=True)

    if com_cor:
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=SolidFillColorMask(
                back_color=(255, 255, 255),
                front_color=AZUL_ESCURO,
            ),
        )
    else:
        img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def gerar_qr_com_legenda(texto, titulo, subtitulo=""):
    """
    Gera um QR Code com moldura e legenda abaixo, pronto para impressão.
    Formato: 400x500 px (cabe ~4 por folha A4).
    """
    # Gera o QR base
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=1,
    )
    qr.add_data(texto)
    qr.make(fit=True)

    qr_img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(
            back_color=(255, 255, 255),
            front_color=AZUL_ESCURO,
        ),
    ).convert("RGB")

    # Cria a imagem final
    largura = 400
    altura = 520
    final = Image.new("RGB", (largura, altura), "white")
    draw = ImageDraw.Draw(final)

    # Moldura
    draw.rectangle(
        [(5, 5), (largura - 6, altura - 6)],
        outline=AZUL_ESCURO,
        width=3,
    )

    # Cola o QR centralizado
    qr_largura = 320
    qr_img = qr_img.resize((qr_largura, qr_largura), Image.LANCZOS)
    x_qr = (largura - qr_largura) // 2
    y_qr = 30
    final.paste(qr_img, (x_qr, y_qr))

    # Tenta carregar fonte; se falhar, usa a padrão
    try:
        fonte_titulo = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
        fonte_sub = ImageFont.truetype("DejaVuSans.ttf", 14)
        fonte_url = ImageFont.truetype("DejaVuSans.ttf", 9)
    except Exception:
        fonte_titulo = ImageFont.load_default()
        fonte_sub = ImageFont.load_default()
        fonte_url = ImageFont.load_default()

    # Título (nome do professor)
    y_texto = y_qr + qr_largura + 20
    _texto_centralizado(draw, titulo, largura, y_texto, fonte_titulo, AZUL_ESCURO)

    # Subtítulo (Nº PM, turma, etc.)
    if subtitulo:
        y_texto += 30
        _texto_centralizado(draw, subtitulo, largura, y_texto, fonte_sub, (100, 100, 100))

    # URL pequena
    y_texto += 40
    _texto_centralizado(draw, "Aponte a câmera do celular", largura,
                        y_texto, fonte_url, (150, 150, 150))
    y_texto += 15
    _texto_centralizado(draw, "para acessar", largura, y_texto, fonte_url, (150, 150, 150))

    buf = BytesIO()
    final.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def _texto_centralizado(draw, texto, largura, y, fonte, cor):
    """Desenha texto centralizado horizontalmente."""
    try:
        bbox = draw.textbbox((0, 0), texto, font=fonte)
        w = bbox[2] - bbox[0]
    except Exception:
        w = draw.textlength(texto, font=fonte)
    x = (largura - w) // 2
    draw.text((x, y), texto, fill=cor, font=fonte)


def link_disponibilidade(nome_professor=None, numero_pm=None):
    """Gera o link de disponibilidade (por Nº PM preferencialmente)."""
    if numero_pm:
        return f"{BASE_URL}/Minha_Disponibilidade?pm={numero_pm}"
    elif nome_professor:
        return f"{BASE_URL}/Minha_Disponibilidade?prof={nome_professor.replace(' ', '+')}"
    return f"{BASE_URL}/Minha_Disponibilidade"


def link_meu_horario(nome_professor=None, numero_pm=None):
    """Gera o link do horário pessoal do professor."""
    if numero_pm:
        return f"{BASE_URL}/Meu_Horario?pm={numero_pm}"
    elif nome_professor:
        return f"{BASE_URL}/Meu_Horario?prof={nome_professor.replace(' ', '+')}"
    return f"{BASE_URL}/Meu_Horario"
