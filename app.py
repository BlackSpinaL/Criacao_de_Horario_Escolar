import streamlit as st

st.set_page_config(
    page_title="Grade Escolar",
    page_icon="🏫",
    layout="wide",
)

st.title("🏫 Sistema de Grade Horária")
st.success("✅ Deploy funcionou! Pipeline GitHub → Streamlit Cloud operacional.")

st.markdown("""
### Próximas etapas
- Etapa 2: banco de dados na nuvem (Supabase)
- Etapa 3: cadastros (professores, turmas, componentes)
- Etapa 4: solver de geração de grade
- Etapa 5: visualização e exportação
""")