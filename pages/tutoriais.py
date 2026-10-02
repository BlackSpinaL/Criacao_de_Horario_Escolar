import streamlit as st
from core.gerar_manual import gerar_manual_bytes

st.set_page_config(page_title="Tutoriais", page_icon="📚", layout="wide")

# =====================================================================
# CABEÇALHO + BOTÃO DE DOWNLOAD DO PDF
# =====================================================================
st.title("📚 Tutoriais e Manual do Usuário")
st.caption(
    "Guia passo a passo para uso do sistema. Você também pode baixar "
    "o manual completo em PDF."
)

col_dl, _ = st.columns([2, 3])
with col_dl:
    try:
        pdf_bytes = gerar_manual_bytes()
        st.download_button(
            "📥 Baixar Manual em PDF",
            pdf_bytes,
            "Manual_Sistema_Grade_Horaria_CTPM.pdf",
            "application/pdf",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")

st.divider()

# =====================================================================
# CONTEÚDO DO TUTORIAL
# =====================================================================
st.header("🎯 Guia rápido de uso")
st.markdown(
    "A ordem abaixo é a **recomendada** para a primeira utilização do "
    "sistema. Uma vez configurado, o uso diário resume-se às etapas 3.4 "
    "e 3.2."
)

st.markdown("""
| Passo | Seção | O que fazer |
|:---:|---|---|
| 1 | **1. Início** | Carregar os dados oficiais (feito uma vez) |
| 2 | **2. Cadastros** | Cadastrar professores, componentes e turmas |
| 3 | **2.4 Matriz Curricular** | Conferir as aulas por série |
| 4 | **2.5 Atribuições** | Vincular professor × disciplina × turma |
| 5 | **3.1 Disponibilidade** | Enviar link para cada professor |
| 6 | **3.2 Gerar Grade** | Gerar a grade (várias versões) |
| 7 | **3.3 Exportar Grade** | Gerar PDF/Excel para imprimir |
| 8 | **3.4 Pendências** | Verificar o que ficou faltando |
| 9 | **4.1 QR Codes** | Distribuir acessos aos professores |
""")

st.divider()

# =====================================================================
# SEÇÕES DETALHADAS
# =====================================================================
with st.expander("1. 🏫 Início", expanded=False):
    st.markdown("""
    A página **Início** mostra um resumo dos dados cadastrados e o botão
    para carregar os dados oficiais do CTPM/Lavras 2026.

    **O que você vê:**
    - Contadores: anos letivos, componentes, turmas, grades, matrizes e itens
    - Botão **🚀 Carregar dados oficiais de 2026** (só aparece com banco vazio)
    - Guia rápido com a ordem recomendada

    **Dica:** Se todos os contadores estiverem em 0, clique no botão para
    carregar os dados oficiais.
    """)

with st.expander("2.1 👨‍🏫 Professores", expanded=False):
    st.markdown("""
    Cadastre o **nome completo** e o **Nº PM** de cada professor.

    **Formato do Nº PM:** `000000-0` (6 dígitos + hífen + 1 dígito)

    **Funcionalidades:**
    - ✅ Cadastro individual ou em lote
    - ✏️ Editar nome e Nº PM a qualquer momento
    - 🔍 Buscar por nome ou Nº PM
    - 🎯 Filtrar por disciplina
    - 📊 Total de aulas calculado automaticamente
    - 👁️ Ver detalhes (turmas e disciplinas de cada professor)
    """)

with st.expander("2.2 📚 Componentes", expanded=False):
    st.markdown("""
    Cadastre cada disciplina do colégio.

    **Funcionalidades:**
    - ✅ Nome, área (Linguagens, Matemática, Ciências, Humanas...)
    - 🧪 Marcar se **tem prática no laboratório**
    - 👨‍👩‍👧 Indique **filha de qual componente** (ex: Ciências/Lab → Ciências)
    - ✏️ Editar qualquer campo
    - 🔍 Filtrar por área e por "tem lab?"
    """)

with st.expander("2.3 🏫 Turmas", expanded=False):
    st.markdown("""
    Cadastre as turmas do ano letivo.

    **Campos:**
    - **Código:** ex: `11801` (8º ano, turma 01)
    - **Série:** ex: `8º ano`
    - **Turno/Segmento:** escolha a grade correspondente
    - **Alunos:** número (opcional)

    **Funcionalidades:**
    - ✏️ Editar turma depois de criada
    - 🔍 Buscar por código ou série
    - 👁️ Ver todas as atribuições de cada turma
    """)

with st.expander("2.4 📖 Matriz Curricular", expanded=False):
    st.markdown("""
    A matriz curricular define **quantas aulas por semana** cada disciplina
    tem em cada série.

    **Como usar:**
    1. Escolha a série no seletor
    2. Os campos **Aulas/sem**, **Grupo** e **Turno extra** são editáveis
    3. Após alterar, clique em **💾 Salvar alterações**

    **Observação:** "Grupo" indica eletivas (IF_ELETIVA). "Turno extra"
    indica que a aula é à tarde (ex: 3º EM).
    """)

with st.expander("2.5 🔗 Atribuições", expanded=False):
    st.markdown("""
    Aqui você vincula cada professor às disciplinas que ele leciona em
    cada turma.

    **Tabela colorida** (comparação matriz × atribuído):
    - 🔵 **Azul** = OK (aulas atribuídas corretamente)
    - 🔴 **Vermelho** = falta atribuir ou faltam aulas
    - 🟡 **Amarelo** = aulas excedem o previsto na matriz

    **Como cadastrar:**
    1. Escolha a turma
    2. Role até **➕ Nova atribuição**
    3. Selecione professor, componente e aulas/sem
    4. Repita até toda a tabela ficar azul

    ⚠️ Se cadastrar mais aulas do que a matriz prevê, o sistema avisa.
    """)

with st.expander("3.1 🚫 Disponibilidade", expanded=False):
    st.markdown("""
    Cada professor acessa a página **Minha Disponibilidade** através de
    um **link individual** e marca os horários em que **PODE** dar aula.

    **Links disponíveis:**
    - 🔗 **Por Nº PM** (recomendado): `.../Minha_Disponibilidade?pm=123456-7`
    - 🔗 **Por nome:** `.../Minha_Disponibilidade?prof=João+Silva`

    **Como funciona:**
    - Professor marca os horários em que **pode** dar aula
    - O sistema cria **automaticamente** as restrições para os horários não marcados
    - Se não marcar nada em um turno, considera que **não pode** naquele turno

    **Também gera planilha em Excel** para quem preferir preencher à mão.
    """)

with st.expander("3.2 🎯 Gerar Grade", expanded=False):
    st.markdown("""
    Clique em **🚀 Gerar nova grade** para rodar o otimizador.

    **O sistema respeita automaticamente:**
    - ✅ Disponibilidade dos professores
    - ✅ Máximo de 2 aulas da mesma disciplina por dia
    - ✅ Sem aulas consecutivas da mesma disciplina
    - ✅ Sem choque de horário entre turmas

    **Versionamento:**
    Cada geração vira uma versão (v1, v2, v3...). Você pode:
    - 👁️ Ver o histórico
    - ♻️ Restaurar uma versão anterior
    - 🗑️ Deletar versões antigas
    """)

with st.expander("3.3 📄 Exportar Grade", expanded=False):
    st.markdown("""
    Gera arquivos prontos para **imprimir e colocar no mural** ou para
    **editar no Excel**.

    **Formatos disponíveis:**

    **📄 PDF (para impressão)**
    - Uma página por turma
    - Formato paisagem (A4)
    - Mostra cada aula com nome da disciplina e do professor
    - Ideal para impressão em massa

    **📊 Excel (para edição)**
    - Uma aba consolidada com TODAS as aulas
    - Uma aba por turma (formato de grade visual)
    - Ideal para ajustes no Excel ou Google Sheets

    **Como usar:**
    1. Escolha o escopo (todas as turmas ou só algumas)
    2. Clique em **🖨️ Gerar PDF** ou **📊 Gerar Excel**
    3. Clique em **⬇️ Baixar** para salvar

    **Pré-visualização:** role até o fim para ver a grade de uma turma
    específica antes de exportar.
    """)

with st.expander("3.4 📊 Pendências", expanded=False):
    st.markdown("""
    O Painel de Pendências mostra o que falta antes de gerar a grade:

    **1️⃣ Disponibilidade dos professores**
    - Quantos preencheram vs. quantos faltam

    **2️⃣ Atribuições incompletas**
    - Turmas com soma diferente da matriz

    **3️⃣ Disciplinas sem professor**
    - Componentes na matriz sem professor atribuído

    **4️⃣ Feedback dos professores**
    - Problemas relatados pelos professores

    ⚠️ **Use este painel ANTES de gerar** para evitar grades incompletas.
    """)

with st.expander("3.5 📅 Meu Horário", expanded=False):
    st.markdown("""
    O professor acessa sua **grade pronta** através de link individual.

    **Funcionalidades:**
    - 📊 Ver grade visual (formato tabela)
    - 📋 Ver lista detalhada de aulas
    - ⚠️ **Reportar problemas** à coordenação
    - 📬 Ver histórico de feedbacks enviados
    """)

with st.expander("4.1 📱 QR Codes", expanded=False):
    st.markdown("""
    Gera QR Codes para os links de cada professor.

    **Como usar:**
    1. Escolha o tipo de página (Disponibilidade ou Horário)
    2. Escolha o formato (QR simples ou com legenda)
    3. Baixe o QR individual ou gere uma folha A4 completa

    **Vantagem:** o professor aponta a câmera do celular e acessa o
    sistema sem precisar digitar link.
    """)

with st.expander("5.1 🗓️ Gerenciar Anos", expanded=False):
    st.markdown("""
    Ferramentas para gerenciar múltiplos anos letivos.

    **Funcionalidades:**
    - 📋 **Duplicar ano:** copia a estrutura (turmas, matrizes, grades)
      para o próximo ano
    - 🎯 **Trocar ano ativo:** define qual ano aparece nas outras páginas
    - 🗑️ **Deletar ano:** remove permanentemente um ano e seus dados

    ⚠️ **Componentes e professores** são compartilhados entre os anos.
    """)

with st.expander("5.2 ⚙️ Configurações", expanded=False):
    st.markdown("""
    Ferramentas administrativas — usar com cuidado.

    **Funcionalidades:**
    - 📥 **Backup dos dados:** baixa tudo em CSV
    - 🗑️ **Zerar sistema:** apaga tudo (dupla confirmação)
    - 🌱 **Carregar dados oficiais:** recarrega o seed 2026
    """)

st.divider()

# =====================================================================
# FAQ
# =====================================================================
st.header("❓ Perguntas frequentes")

faqs = [
    ("Não consigo conectar ao banco de dados",
     "Aguarde 2 minutos e recarregue a página. O Supabase fecha "
     "conexões antigas automaticamente."),
    ("A grade não gera",
     "Verifique em **📊 Pendências** se todas as turmas estão com "
     "atribuições completas (tabela azul)."),
    ("Não consigo deletar um professor",
     "Professores com aulas atribuídas pedem confirmação. Marque o "
     "checkbox e clique em Deletar."),
    ("O Nº PM foi cadastrado errado",
     "Use a seção **✏️ Editar professor** na página de Professores."),
    ("Perdi o backup dos dados",
     "Baixe um novo em **⚙️ Configurações → 📥 Backup dos dados**."),
    ("Como começar do zero?",
     "**⚙️ Configurações → 🗑️ Zerar sistema** (digite ZERAR e marque "
     "o checkbox). Depois volte em Início e clique em Carregar dados."),
    ("O professor não consegue acessar o link",
     "Verifique se o link está correto. Tente o link por Nº PM ou "
     "gere um QR Code em **📱 QR Codes**."),
    ("O PDF ficou com muitas páginas, dá para reduzir?",
     "Sim! Em **📄 Exportar Grade**, escolha **Selecionar turmas "
     "específicas** e marque apenas as que deseja incluir no PDF."),
    ("Como editar a grade depois de gerada?",
     "Você pode: (1) gerar uma nova versão em **🎯 Gerar Grade**, "
     "(2) restaurar uma versão anterior, ou (3) exportar para Excel "
     "em **📄 Exportar Grade** e editar manualmente."),
]

for i, (pergunta, resposta) in enumerate(faqs, start=1):
    with st.expander(f"{i}. {pergunta}", expanded=False):
        st.markdown(resposta)

st.divider()

st.caption(
    "💡 **Dica:** Para suporte adicional, entre em contato com a coordenação. "
    "O manual completo em PDF está disponível no botão acima."
)
