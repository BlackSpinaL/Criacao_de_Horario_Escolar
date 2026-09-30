import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Atribuições", page_icon="🔗", layout="wide")
st.title("🔗 Atribuições — Professor × Componente × Turma")

engine = get_engine()

# ---------- Carrega listas ----------
with engine.connect() as conn:
    profs = pd.read_sql(text("SELECT id, nome FROM professores ORDER BY nome"), conn)
    comps = pd.read_sql(text("SELECT id, nome FROM componentes ORDER BY nome"), conn)
    turmas = pd.read_sql(
        text("SELECT id, nome, serie, segmento FROM turmas ORDER BY codigo"),
        conn,
    )

if profs.empty:
    st.warning("⚠️ Cadastre professores primeiro (menu lateral → Professores).")
    st.stop()
if comps.empty or turmas.empty:
    st.warning("⚠️ Rode o seed 2026 na página inicial para carregar componentes e turmas.")
    st.stop()

# ---------- Cadastro ----------
with st.form("nova_atv", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    prof_nome = c1.selectbox("Professor", profs["nome"])
    comp_nome = c2.selectbox("Componente", comps["nome"])
    turma_nome = c3.selectbox("Turma", turmas["nome"])
    aulas = c4.number_input("Aulas/sem", 1, 10, 2)

    if st.form_submit_button("➕ Adicionar", type="primary"):
        prof_id = int(profs.loc[profs["nome"] == prof_nome, "id"].iloc[0])
        comp_id = int(comps.loc[comps["nome"] == comp_nome, "id"].iloc[0])
        turma_id = int(turmas.loc[turmas["nome"] == turma_nome, "id"].iloc[0])

        try:
            with engine.begin() as conn:
                ano_id = conn.execute(
                    text("SELECT id FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
                ).scalar()
                existe = conn.execute(text(
                    "SELECT id FROM atividades WHERE ano_letivo_id = :a "
                    "AND professor_id = :p AND componente_id = :c "
                    "AND turma_id = :t"
                ), {"a": ano_id, "p": prof_id, "c": comp_id, "t": turma_id}).first()

                if existe:
                    st.warning("⚠️ Essa atribuição já existe.")
                else:
                    conn.execute(text(
                        "INSERT INTO atividades (ano_letivo_id, professor_id, "
                        "componente_id, turma_id, aulas_semana) "
                        "VALUES (:a, :p, :c, :t, :n)"
                    ), {"a": ano_id, "p": prof_id, "c": comp_id,
                        "t": turma_id, "n": aulas})
                    st.success("✅ Atribuição adicionada!")
                    st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

# ---------- Lista ----------
with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT a.id, p.nome AS professor, c.nome AS componente,
               t.nome AS turma, a.aulas_semana
        FROM atividades a
        JOIN professores p ON p.id = a.professor_id
        JOIN componentes c ON c.id = a.componente_id
        JOIN turmas t ON t.id = a.turma_id
        ORDER BY p.nome, t.nome, c.nome
    """), conn)

st.subheader(f"Atribuições cadastradas ({len(df)})")

if df.empty:
    st.info("Nenhuma atribuição ainda. Use o formulário acima.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

    remover = st.selectbox("Remover ID", [""] + df["id"].tolist())
    if remover and st.button("🗑️ Remover"):
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM atividades WHERE id = :id"),
                {"id": int(remover)},
            )
        st.success("Removida!")
        st.rerun()
