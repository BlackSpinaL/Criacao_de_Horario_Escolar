import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Matriz Curricular", page_icon="📚", layout="wide")
st.title("📚 Matriz Curricular")
st.caption("Grade oficial de componentes e aulas semanais por série.")

engine = get_engine()

with engine.connect() as conn:
    ano_id = conn.execute(
        text("SELECT id FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
    ).scalar()

if ano_id is None:
    st.warning("Rode o seed 2026 primeiro.")
    st.stop()

with engine.connect() as conn:
    series = pd.read_sql(text(
        "SELECT DISTINCT serie, segmento FROM matrizes "
        "WHERE ano_letivo_id = :a ORDER BY segmento, serie"
    ), conn, params={"a": ano_id})

if series.empty:
    st.info("Nenhuma matriz cadastrada.")
    st.stop()

serie_sel = st.selectbox(
    "Série",
    series["serie"].tolist(),
    index=series["serie"].tolist().index("8º ano") if "8º ano" in series["serie"].tolist() else 0,
)

with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT c.nome AS "Componente", c.area AS "Área",
               im.aulas_semana AS "Aulas/sem",
               im.aulas_semana * 40 AS "Aulas/ano",
               im.grupo_opcao AS "Grupo",
               im.turno_extra AS "Turno extra"
        FROM matrizes m
        JOIN itens_matriz im ON im.matriz_id = m.id
        JOIN componentes c   ON c.id = im.componente_id
        WHERE m.ano_letivo_id = :a AND m.serie = :s
        ORDER BY c.area, c.nome
    """), conn, params={"a": ano_id, "s": serie_sel})

st.subheader(f"Matriz — {serie_sel}")

# Estatísticas
total_sem = int(df["Aulas/sem"].sum())
c1, c2, c3 = st.columns(3)
c1.metric("Componentes", len(df))
c2.metric("Aulas semanais", total_sem)
c3.metric("Aulas anuais", total_sem * 40)

st.dataframe(df, use_container_width=True, hide_index=True)

st.caption(
    "💡 **Grupo** indica eletivas (IF_ELETIVA) — o aluno escolhe apenas uma "
    "das opções. **Turno extra** indica que a aula é à tarde (3º EM)."
)
