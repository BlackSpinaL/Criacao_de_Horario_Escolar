import streamlit as st
from sqlalchemy import text
from core.db import get_engine
from core.seed_2026 import rodar_seed, status_banco

st.set_page_config(
    page_title="Grade Escolar CTPM",
    page_icon="🏫",
    layout="wide",
)

# =====================================================================
# PÁGINA INICIAL (Início)
# =====================================================================
def pagina_inicio():
    st.title("🏫 Sistema de Grade Horária")
    st.caption("CTPM/Lavras — Ano Letivo 2026")

    # Testa conexão
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        st.error(f"❌ Erro ao conectar no banco: {e}")
        st.stop()

    stats = status_banco()

    st.subheader("📊 Dados cadastrados")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Anos letivos", stats["anos"])
        st.metric("Componentes", stats["componentes"])
        st.metric("Turmas", stats["turmas"])
    with col2:
        st.metric("Grades de horário", stats["grades"])
        st.metric("Slots de horário", stats["slots"])
        st.metric("Matrizes", stats["matrizes"])
    with col3:
        st.metric("Itens de matriz", stats["itens"])

    st.divider()

    st.subheader("🌱 Carga inicial 2026")

    if stats["anos"] == 0:
        st.info(
            "Banco vazio. Clique no botão abaixo para **carregar os dados "
            "oficiais do CTPM/Lavras 2026**. Depois você pode **editar tudo "
            "livremente** pelas páginas de cada cadastro."
        )
        if st.button("🚀 Carregar dados oficiais de 2026", type="primary"):
            with st.spinner("Inserindo dados no banco..."):
                msg = rodar_seed()
            st.success(msg)
            st.balloons()
            st.rerun()
    else:
        st.success(
            "✅ Os dados de 2026 já estão carregados no banco. "
            "Você pode editá-los livremente pelas páginas de cada cadastro."
        )

    st.divider()

    # Guia rápido de uso
    st.subheader("🧭 Guia rápido")
    st.markdown("""
    **Siga esta ordem para configurar o sistema:**

    1. **🏫 Início** — carregue os dados oficiais (feito uma vez)
    2. **📋 Cadastros** — cadastre professores, componentes, turmas
    3. **📖 Matriz Curricular** — confira as aulas por série
    4. **🔗 Atribuições** — vincule professor × disciplina × turma
    5. **🚫 Disponibilidade** — envie o link para cada professor
    6. **🎯 Gerar Grade** — gere a grade (pode ser várias versões)
    7. **📊 Pendências** — verifique o que ficou faltando
    8. **📱 QR Codes** — distribua os acessos aos professores
    """)


# =====================================================================
# ESTRUTURA DO MENU LATERAL (com numeração e seções)
# =====================================================================
paginas = {
    "2. 📋 CADASTROS": [
        st.Page("pages/professores.py", title="2.1 👨‍🏫 Professores", icon="👨‍🏫"),
        st.Page("pages/componentes.py", title="2.2 📚 Componentes", icon="📚"),
        st.Page("pages/turmas.py", title="2.3 🏫 Turmas", icon="🏫"),
        st.Page("pages/matriz.py", title="2.4 📖 Matriz Curricular", icon="📖"),
        st.Page("pages/atribuicoes.py", title="2.5 🔗 Atribuições", icon="🔗"),
    ],
    "3. 🎯 GRADE HORÁRIA": [
        st.Page("pages/disponibilidade.py", title="3.1 🚫 Disponibilidade", icon="🚫"),
        st.Page("pages/gerar.py", title="3.2 🎯 Gerar Grade", icon="🎯"),
        st.Page("pages/pendencias.py", title="3.3 📊 Pendências", icon="📊"),
        st.Page("pages/meu_horario.py", title="3.4 📅 Meu Horário", icon="📅"),
    ],
    "4. 📱 EXTRAS": [
        st.Page("pages/qr_codes.py", title="4.1 📱 QR Codes", icon="📱"),
    ],
    "5. ⚙️ ADMINISTRAÇÃO": [
        st.Page("pages/gerenciar_anos.py", title="5.1 🗓️ Gerenciar Anos", icon="🗓️"),
        st.Page("pages/configuracoes.py", title="5.2 ⚙️ Configurações", icon="⚙️"),
    ],
    "6. 📚 TUTORIAIS": [
        st.Page("pages/tutoriais.py", title="6.1 📖 Manual do Usuário", icon="📚"),
    ],
}

# =====================================================================
# MONTA A NAVEGAÇÃO
# =====================================================================
inicio = st.Page(pagina_inicio, title="1. 🏫 Início", icon="🏫", default=True)

navegacao = {
    "1. 🏫 INÍCIO": [inicio],
    **paginas,
}

pg = st.navigation(navegacao)
pg.run()
