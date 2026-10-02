"""Gera o manual do usuário em PDF usando reportlab."""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether,
)


AZUL = HexColor("#1F4E78")
AZUL_CLARO = HexColor("#D6EAF8")
CINZA = HexColor("#7F8C8D")


def _estilos():
    s = getSampleStyleSheet()
    return {
        "titulo_capa": ParagraphStyle(
            "titulo_capa", parent=s["Title"],
            fontSize=26, textColor=AZUL, spaceAfter=20, alignment=TA_CENTER,
        ),
        "subtitulo_capa": ParagraphStyle(
            "subtitulo_capa", parent=s["Normal"],
            fontSize=14, textColor=CINZA, spaceAfter=10, alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "h1", parent=s["Heading1"],
            fontSize=18, textColor=AZUL, spaceBefore=18, spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2", parent=s["Heading2"],
            fontSize=14, textColor=AZUL, spaceBefore=12, spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "h3", parent=s["Heading3"],
            fontSize=11, textColor=HexColor("#2874A6"),
            spaceBefore=8, spaceAfter=4,
        ),
        "corpo": ParagraphStyle(
            "corpo", parent=s["BodyText"],
            fontSize=10.5, spaceAfter=6, alignment=TA_JUSTIFY,
        ),
        "passo": ParagraphStyle(
            "passo", parent=s["BodyText"],
            fontSize=10.5, spaceAfter=4, leftIndent=18, bulletIndent=6,
        ),
        "nota": ParagraphStyle(
            "nota", parent=s["BodyText"],
            fontSize=9.5, textColor=CINZA, spaceAfter=4, leftIndent=12,
        ),
    }


def _cabecalho_rodape(canvas, doc):
    """Desenha o cabeçalho e rodapé de cada página."""
    canvas.saveState()
    largura, altura = A4

    canvas.setFillColor(AZUL)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(2 * cm, altura - 1.2 * cm, "CTPM/Lavras — Sistema de Grade Horária")
    canvas.setStrokeColor(AZUL)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, altura - 1.4 * cm, largura - 2 * cm, altura - 1.4 * cm)

    canvas.setFillColor(CINZA)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(largura / 2, 1.2 * cm, f"Página {doc.page}")
    canvas.drawString(2 * cm, 0.8 * cm, "Manual do Usuário — 2026")
    canvas.drawRightString(largura - 2 * cm, 0.8 * cm,
                          datetime.now().strftime("%d/%m/%Y"))

    canvas.restoreState()


def gerar_manual_bytes():
    """Gera o manual completo em PDF e devolve os bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Manual do Sistema de Grade Horária — CTPM/Lavras",
        author="CTPM/Lavras",
    )

    e = _estilos()
    story = []

    # ==================================================================
    # CAPA
    # ==================================================================
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("📚 Manual do Usuário", e["titulo_capa"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Sistema de Grade Horária — CTPM/Lavras",
        e["subtitulo_capa"],
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Ano Letivo 2026", e["subtitulo_capa"]))
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph(
        "Este manual apresenta, passo a passo, todas as funcionalidades "
        "do sistema. Siga a ordem apresentada para configurar e operar "
        "o sistema corretamente.",
        e["corpo"],
    ))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        e["nota"],
    ))
    story.append(PageBreak())

    # ==================================================================
    # GUIA RÁPIDO
    # ==================================================================
    story.append(Paragraph("🎯 Guia rápido de uso", e["h1"]))
    story.append(Paragraph(
        "A ordem abaixo é a recomendada para a primeira utilização do "
        "sistema. Uma vez configurado, o uso diário resume-se às etapas "
        "3.4 e 3.2.", e["corpo"],
    ))
    story.append(Spacer(1, 0.3 * cm))

    dados_guia = [
        ["Passo", "Seção", "O que fazer"],
        ["1", "1. Início", "Carregar os dados oficiais (feito uma vez)"],
        ["2", "2. Cadastros", "Cadastrar professores, componentes e turmas"],
        ["3", "2.4 Matriz", "Conferir as aulas por série"],
        ["4", "2.5 Atribuições", "Vincular professor × disciplina × turma"],
        ["5", "3.1 Disponibilidade", "Enviar link para cada professor"],
        ["6", "3.2 Gerar Grade", "Gerar a grade (várias versões)"],
        ["7", "3.3 Exportar Grade", "Gerar PDF/Excel para imprimir"],
        ["8", "3.4 Pendências", "Verificar o que ficou faltando"],
        ["9", "4.1 QR Codes", "Distribuir acessos aos professores"],
    ]
    t = Table(dados_guia, colWidths=[1.5 * cm, 3.5 * cm, 11 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [HexColor("#F8F9FA"), HexColor("#FFFFFF")]),
        ("GRID", (0, 0), (-1, -1), 0.5, CINZA),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ==================================================================
    # SEÇÃO 1
    # ==================================================================
    story.append(Paragraph("1. 🏫 Início", e["h1"]))
    story.append(Paragraph(
        "A página <b>Início</b> mostra um resumo dos dados cadastrados e "
        "o botão para carregar os dados oficiais do CTPM/Lavras 2026.",
        e["corpo"],
    ))
    story.append(Paragraph("O que você vê nesta tela:", e["h3"]))
    story.append(Paragraph("• Contadores de: anos letivos, componentes, turmas, "
                          "grades, matrizes e itens.", e["passo"]))
    story.append(Paragraph("• Botão <b>🚀 Carregar dados oficiais de 2026</b> "
                          "(aparece só quando o banco está vazio).", e["passo"]))
    story.append(Paragraph("• Guia rápido de uso com a ordem recomendada.",
                          e["passo"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "<b>Dica:</b> Se todos os contadores estiverem em 0, clique no botão "
        "para carregar os dados oficiais. Você poderá editar tudo depois.",
        e["nota"],
    ))
    story.append(PageBreak())

    # ==================================================================
    # SEÇÃO 2 — CADASTROS
    # ==================================================================
    story.append(Paragraph("2. 📋 Cadastros", e["h1"]))
    story.append(Paragraph(
        "Esta seção contém todos os cadastros básicos necessários antes "
        "de gerar a grade.",
        e["corpo"],
    ))

    # 2.1
    story.append(Paragraph("2.1 👨‍🏫 Professores", e["h2"]))
    story.append(Paragraph("Cadastre o nome completo e o Nº PM de cada professor.",
                          e["corpo"]))
    story.append(Paragraph("• <b>Nº PM:</b> formato <b>000000-0</b> "
                          "(6 dígitos + hífen + 1 dígito).", e["passo"]))
    story.append(Paragraph("• O sistema calcula automaticamente o total de aulas "
                          "por professor.", e["passo"]))
    story.append(Paragraph("• Use a seção <b>✏️ Editar professor</b> para "
                          "corrigir nome/Nº PM.", e["passo"]))

    # 2.2
    story.append(Paragraph("2.2 📚 Componentes", e["h2"]))
    story.append(Paragraph("Cadastre cada disciplina do colégio.",
                          e["corpo"]))
    story.append(Paragraph("• Marque <b>tem prática no laboratório</b> quando aplicável.",
                          e["passo"]))
    story.append(Paragraph("• Indique <b>é filha de qual componente</b> para "
                          "disciplinas vinculadas (ex: Ciências/Lab → Ciências).",
                          e["passo"]))

    # 2.3
    story.append(Paragraph("2.3 🏫 Turmas", e["h2"]))
    story.append(Paragraph("Cadastre as turmas do ano letivo.",
                          e["corpo"]))
    story.append(Paragraph("• <b>Código:</b> ex: 11801 (8º ano, turma 01).",
                          e["passo"]))
    story.append(Paragraph("• <b>Série:</b> ex: 8º ano.", e["passo"]))
    story.append(Paragraph("• <b>Turno/Segmento:</b> escolha a grade correspondente.",
                          e["passo"]))

    # 2.4
    story.append(Paragraph("2.4 📖 Matriz Curricular", e["h2"]))
    story.append(Paragraph(
        "A matriz curricular define quantas aulas por semana cada disciplina "
        "tem em cada série. Os campos <b>Aulas/sem</b>, <b>Grupo</b> e "
        "<b>Turno extra</b> são editáveis diretamente na tabela.",
        e["corpo"],
    ))
    story.append(Paragraph(
        "<b>Dica:</b> após editar, clique em <b>💾 Salvar alterações</b>.",
        e["nota"],
    ))

    # 2.5
    story.append(Paragraph("2.5 🔗 Atribuições", e["h2"]))
    story.append(Paragraph(
        "Aqui você vincula cada professor às disciplinas que ele leciona "
        "em cada turma. O sistema mostra uma tabela colorida comparando a "
        "matriz com o atribuído:",
        e["corpo"],
    ))
    story.append(Paragraph("• <b>🔵 Azul</b> = OK (aulas atribuídas corretamente).",
                          e["passo"]))
    story.append(Paragraph("• <b>🔴 Vermelho</b> = falta atribuir ou faltam aulas.",
                          e["passo"]))
    story.append(Paragraph("• <b>🟡 Amarelo</b> = aulas excedem o previsto.",
                          e["passo"]))
    story.append(PageBreak())

    # ==================================================================
    # SEÇÃO 3 — GRADE HORÁRIA
    # ==================================================================
    story.append(Paragraph("3. 🎯 Grade Horária", e["h1"]))
    story.append(Paragraph(
        "Esta seção contém o coração do sistema: a geração e gestão da "
        "grade horária.",
        e["corpo"],
    ))

    # 3.1
    story.append(Paragraph("3.1 🚫 Disponibilidade", e["h2"]))
    story.append(Paragraph(
        "Cada professor acessa a página <b>Minha Disponibilidade</b> através "
        "de um link individual e marca os horários em que <b>PODE</b> dar aula.",
        e["corpo"],
    ))
    story.append(Paragraph("• Links disponíveis: <b>por Nº PM</b> (recomendado) "
                          "e <b>por nome</b>.", e["passo"]))
    story.append(Paragraph("• O sistema cria automaticamente as restrições "
                          "com base no que <b>não</b> foi marcado.", e["passo"]))
    story.append(Paragraph("• Gera também planilha em Excel para quem "
                          "preferir preencher à mão.", e["passo"]))

    # 3.2
    story.append(Paragraph("3.2 🎯 Gerar Grade", e["h2"]))
    story.append(Paragraph(
        "Clique em <b>🚀 Gerar nova grade</b> para rodar o otimizador. "
        "O sistema respeita automaticamente:",
        e["corpo"],
    ))
    story.append(Paragraph("• Disponibilidade dos professores.", e["passo"]))
    story.append(Paragraph("• Máximo de 2 aulas da mesma disciplina por dia.",
                          e["passo"]))
    story.append(Paragraph("• Sem aulas consecutivas da mesma disciplina.",
                          e["passo"]))
    story.append(Paragraph("• Sem choque de horário entre turmas.", e["passo"]))
    story.append(Paragraph(
        "<b>Versionamento:</b> cada geração vira uma versão (v1, v2, v3...). "
        "Você pode restaurar versões anteriores quando quiser.",
        e["nota"],
    ))

    # 3.3 — NOVO
    story.append(Paragraph("3.3 📄 Exportar Grade", e["h2"]))
    story.append(Paragraph(
        "Gera arquivos prontos para imprimir e colocar no mural, ou para "
        "editar no Excel.",
        e["corpo"],
    ))
    story.append(Paragraph("<b>Formatos disponíveis:</b>", e["passo"]))
    story.append(Paragraph(
        "• <b>📄 PDF (para impressão):</b> uma página por turma, formato "
        "paisagem (A4). Mostra cada aula com nome da disciplina e do professor. "
        "Ideal para impressão em massa.", e["passo"],
    ))
    story.append(Paragraph(
        "• <b>📊 Excel (para edição):</b> uma aba consolidada com todas as "
        "aulas + uma aba por turma. Ideal para ajustes no Excel ou Google "
        "Sheets.", e["passo"],
    ))
    story.append(Paragraph("<b>Como usar:</b>", e["passo"]))
    story.append(Paragraph("1. Escolha o escopo (todas as turmas ou algumas).",
                          e["passo"]))
    story.append(Paragraph("2. Clique em <b>🖨️ Gerar PDF</b> ou <b>📊 Gerar Excel</b>.",
                          e["passo"]))
    story.append(Paragraph("3. Clique em <b>⬇️ Baixar</b> para salvar o arquivo.",
                          e["passo"]))
    story.append(Paragraph(
        "<b>Pré-visualização:</b> no fim da página, você pode ver a grade de "
        "uma turma específica antes de exportar.",
        e["nota"],
    ))

    # 3.4
    story.append(Paragraph("3.4 📊 Pendências", e["h2"]))
    story.append(Paragraph(
        "O Painel de Pendências mostra, em 4 seções, o que falta antes de "
        "gerar a grade:",
        e["corpo"],
    ))
    story.append(Paragraph("• Professores que não preencheram disponibilidade.",
                          e["passo"]))
    story.append(Paragraph("• Turmas com atribuições incompletas.", e["passo"]))
    story.append(Paragraph("• Disciplinas sem professor.", e["passo"]))
    story.append(Paragraph("• Feedbacks enviados pelos professores.", e["passo"]))

    # 3.5
    story.append(Paragraph("3.5 📅 Meu Horário", e["h2"]))
    story.append(Paragraph(
        "O professor acessa sua grade pronta através de link individual. "
        "Pode reportar problemas diretamente à coordenação.",
        e["corpo"],
    ))
    story.append(PageBreak())

    # ==================================================================
    # SEÇÃO 4 — EXTRAS
    # ==================================================================
    story.append(Paragraph("4. 📱 Extras", e["h1"]))

    story.append(Paragraph("4.1 📱 QR Codes", e["h2"]))
    story.append(Paragraph(
        "Gera QR Codes para os links de cada professor. Você pode:",
        e["corpo"],
    ))
    story.append(Paragraph("• Visualizar e baixar o QR Code individual.", e["passo"]))
    story.append(Paragraph("• Gerar uma folha A4 com todos os QRs para imprimir "
                          "e recortar.", e["passo"]))
    story.append(Paragraph("• O professor aponta a câmera do celular e acessa "
                          "o sistema direto.", e["passo"]))
    story.append(PageBreak())

    # ==================================================================
    # SEÇÃO 5 — ADMINISTRAÇÃO
    # ==================================================================
    story.append(Paragraph("5. ⚙️ Administração", e["h1"]))
    story.append(Paragraph(
        "Ferramentas administrativas — usar com cuidado.",
        e["corpo"],
    ))

    story.append(Paragraph("5.1 🗓️ Gerenciar Anos", e["h2"]))
    story.append(Paragraph("• <b>Duplicar ano letivo:</b> copia a estrutura "
                          "(turmas, matrizes, grades) para o próximo ano.",
                          e["passo"]))
    story.append(Paragraph("• <b>Trocar ano ativo:</b> define qual ano aparece "
                          "nas outras páginas.", e["passo"]))
    story.append(Paragraph("• <b>Deletar ano:</b> remove permanentemente um ano "
                          "e seus dados.", e["passo"]))

    story.append(Paragraph("5.2 ⚙️ Configurações", e["h2"]))
    story.append(Paragraph("• <b>📥 Backup:</b> baixa todos os dados em CSV.",
                          e["passo"]))
    story.append(Paragraph("• <b>🗑️ Zerar sistema:</b> apaga tudo (dupla "
                          "confirmação).", e["passo"]))
    story.append(Paragraph("• <b>🌱 Carregar dados:</b> recarrega o seed 2026.",
                          e["passo"]))
    story.append(PageBreak())

    # ==================================================================
    # SEÇÃO 6 — TUTORIAIS
    # ==================================================================
    story.append(Paragraph("6. 📚 Tutoriais", e["h1"]))
    story.append(Paragraph(
        "Esta seção oferece dois recursos de apoio:",
        e["corpo"],
    ))
    story.append(Paragraph(
        "• <b>6.1 Manual do Usuário:</b> guia passo a passo dentro do próprio "
        "sistema, com expanders para cada seção. Você também pode baixar este "
        "PDF clicando em <b>📥 Baixar Manual em PDF</b>.",
        e["passo"],
    ))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "<b>Dica:</b> Recomendamos ler o manual completo (este PDF) antes de "
        "começar a usar o sistema, e consultar a página 6.1 sempre que tiver "
        "dúvidas rápidas.",
        e["nota"],
    ))
    story.append(PageBreak())

    # ==================================================================
    # FAQ
    # ==================================================================
    story.append(Paragraph("❓ Perguntas frequentes", e["h1"]))

    faqs = [
        ("Não consigo conectar ao banco de dados",
         "Aguarde 2 minutos e recarregue a página. O Supabase fecha "
         "conexões antigas automaticamente."),
        ("A grade não gera",
         "Verifique em <b>📊 Pendências</b> se todas as turmas estão com "
         "atribuições completas (tabela azul)."),
        ("Não consigo deletar um professor",
         "Professores com aulas atribuídas pedem confirmação. Marque o "
         "checkbox e clique em Deletar."),
        ("O Nº PM foi cadastrado errado",
         "Use a seção <b>✏️ Editar professor</b> na página de Professores."),
        ("Perdi o backup dos dados",
         "Baixe um novo em <b>⚙️ Configurações → 📥 Backup dos dados</b>."),
        ("Como começar do zero?",
         "<b>⚙️ Configurações → 🗑️ Zerar sistema</b> (digite ZERAR e "
         "marque o checkbox). Depois volte em Início e clique em "
         "Carregar dados."),
        ("O professor não consegue acessar o link",
         "Verifique se o link está correto. Tente o link por Nº PM ou "
         "gere um QR Code em <b>📱 QR Codes</b>."),
        ("O PDF ficou com muitas páginas, dá para reduzir?",
         "Sim! Em <b>📄 Exportar Grade</b>, escolha <b>Selecionar turmas "
         "específicas</b> e marque apenas as que deseja incluir."),
        ("Como editar a grade depois de gerada?",
         "Você pode: (1) gerar uma nova versão em <b>🎯 Gerar Grade</b>, "
         "(2) restaurar uma versão anterior, ou (3) exportar para Excel "
         "em <b>📄 Exportar Grade</b> e editar manualmente."),
    ]

    for pergunta, resposta in faqs:
        story.append(Paragraph(f"<b>{pergunta}</b>", e["h3"]))
        story.append(Paragraph(resposta, e["corpo"]))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        "<i>Para mais informações ou suporte, entre em contato com a "
        "coordenação.</i>", e["nota"],
    ))

    doc.build(story, onFirstPage=_cabecalho_rodape,
              onLaterPages=_cabecalho_rodape)

    buf.seek(0)
    return buf.getvalue()
