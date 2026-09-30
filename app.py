import streamlit as st
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(
    page_title="Grade Escolar",
    page_icon="🏫",
    layout="wide",
)

st.title("🏫 Sistema de Grade Horária")

# ---------- Testa conexão com o banco ----------
st.subheader("🔌 Status do banco de dados")

try:
    engine = get_engine()
    with engine.connect() as conn:
        resultado = conn.execute(
            text("SELECT COUNT(*) FROM anos_letivos")
        ).scalar()

    st.success(f"✅ Conectado ao banco com sucesso! ({resultado} anos letivos cadastrados)")

except Exception as e:
    st.error(f"❌ Erro ao conectar no banco: {e}")
    st.info("Verifique se o Secrets do Streamlit Cloud está correto (Etapa 2.5).")
    st.stop()

# ---------- Próximas etapas ----------
st.markdown("""
### Próximas etapas
- ✅ Etapa 1: deploy no Streamlit Cloud
- ✅ Etapa 2: banco de dados na nuvem (Supabase)
- ⏳ Etapa 3: cadastros (professores, turmas, componentes)
- ⏳ Etapa 4: solver de geração de grade
- ⏳ Etapa 5: visualização e exportação
""")
