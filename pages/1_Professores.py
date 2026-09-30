import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Professores", page_icon="👨‍🏫", layout="wide")
st.title("👨‍🏫 Professores")

engine = get_engine()

# ---------- Cadastro ----------
with st.form("novo_prof", clear_on_submit=True):
    c1, c2, c3 = st.columns([3, 1, 3])
    nome = c1.text_input("Nome do professor(a)")
    carga = c2.number_input("Carga máx. (aulas/sem)", 1, 60, 40)
    email = c3.text_input("E-mail (opcional)")

    if st.form_submit_button("➕ Adicionar", type="primary"):
        if not nome.strip():
            st.error("Informe o nome.")
        else:
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        "INSERT INTO professores (nome, carga_max, email) "
                        "VALUES (:n, :c, :e)"
                    ), {"n": nome.strip(), "c": carga, "e": email.strip() or None})
                st.success(f"✅ {nome} cadastrado(a)!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

# ---------- Lista ----------
with engine.connect() as conn:
    df = pd.read_sql(
        text("SELECT id, nome, carga_max, email FROM professores ORDER BY nome"),
        conn,
    )

st.subheader(f"Cadastrados ({len(df)})")

if df.empty:
    st.info("Nenhum professor cadastrado ainda. Use o formulário acima.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

    nomes = dict(zip(df["id"], df["nome"]))
    remover = st.selectbox(
        "Remover professor",
        [""] + df["id"].tolist(),
        format_func=lambda x: nomes.get(x, "—"),
    )
    if remover and st.button("🗑️ Remover"):
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM professores WHERE id = :id"),
                {"id": int(remover)},
            )
        st.success("Removido!")
        st.rerun()
