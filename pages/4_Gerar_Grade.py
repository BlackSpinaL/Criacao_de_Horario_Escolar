import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine
from core.solver import gerar_grade

st.set_page_config(page_title="Gerar Grade", page_icon="🎯", layout="wide")
st.title("🎯 Gerar Grade Horária")

engine = get_engine()
with engine.connect() as conn:
    n_atv = conn.execute(text("SELECT COUNT(*) FROM atividades")).scalar()
    n_grade = conn.execute(text("SELECT COUNT(*) FROM grade_gerada")).scalar()
    n_rest = conn.execute(text("SELECT COUNT(*) FROM restricoes_professor")).scalar()

c1, c2, c3 = st.columns(3)
c1.metric("Atribuições", n_atv)
c2.metric("Alocações na grade atual", n_grade)
c3.metric("Restrições de professor", n_rest)

st.divider()

if n_atv == 0:
    st.warning("⚠️ Cadastre atribuições primeiro (página Atribuições).")
    st.stop()

if st.button("🚀 Gerar grade", type="primary"):
    with st.spinner("Rodando o solver... isso pode levar alguns segundos."):
        resultado = gerar_grade(timeout_segundos=30)

    if "erro" in resultado:
        st.error(f"❌ {resultado['erro']}")
    else:
        st.success(
            f"✅ Grade gerada! {resultado['total_alocacoes']} alocações "
            f"em {resultado['tempo']}s (status: {resultado['status']})."
        )
        st.balloons()
        st.rerun()

if n_grade > 0:
    st.subheader(f"📋 Grade atual ({n_grade} alocações)")

    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT p.nome AS professor, c.nome AS componente,
                   t.nome AS turma, h.dia, h.ordem, h.inicio, h.fim
            FROM grade_gerada g
            JOIN atividades a ON a.id = g.atividade_id
            JOIN professores p ON p.id = a.professor_id
            JOIN componentes c ON c.id = a.componente_id
            JOIN turmas t     ON t.id = a.turma_id
            JOIN horarios h   ON h.id = g.horario_id
            ORDER BY t.nome, h.dia, h.ordem
        """), conn)

    filtro = st.selectbox("Filtrar por turma", ["Todas"] + sorted(df["turma"].unique()))
    if filtro != "Todas":
        df = df[df["turma"] == filtro]

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️ Baixar CSV",
        df.to_csv(index=False).encode("utf-8"),
        "grade_gerada.csv",
        "text/csv",
    )
