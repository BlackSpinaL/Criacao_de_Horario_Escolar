import streamlit as st
from sqlalchemy import text
from core.db import get_engine
from core.seed_2026 import rodar_seed, status_banco

st.set_page_config(
    page_title="Grade Escolar",
    page_icon="🏫",
    layout="wide",
)

st.title("🏫 Sistema de Grade Horária")

# ---------- Testa conexão ----------
try:
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    st.error(f"❌ Erro ao conectar no banco: {e}")
    st.stop()

# ---------- Estatísticas ----------
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

# ---------- Carga inicial 2026 ----------
st.subheader("🌱 Carga inicial 2026")

if stats["anos"] == 0:
    st.info(
        "Banco vazio. Clique no botão abaixo para **carregar os dados "
        "oficiais do CTPM/Lavras 2026**. Depois você pode **editar tudo "
        "livremente** pelas páginas de cada cadastro (componentes, matrizes, "
        "turmas, etc.)."
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
