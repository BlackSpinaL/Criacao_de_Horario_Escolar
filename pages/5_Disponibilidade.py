import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Disponibilidade", page_icon="🚫", layout="wide")
st.title("🚫 Disponibilidade dos Professores")
st.caption("Marque os horários em que cada professor NÃO PODE dar aula.")

engine = get_engine()

with engine.connect() as conn:
    profs = pd.read_sql(
        text("SELECT id, nome FROM professores ORDER BY nome"), conn
    )
    grades = pd.read_sql(
        text("SELECT id, titulo, dias_semana FROM grades_horarias ORDER BY id"),
        conn,
    )

if profs.empty or grades.empty:
    st.warning("Cadastre professores e rode o seed primeiro.")
    st.stop()

c1, c2 = st.columns(2)
prof_nome = c1.selectbox("Professor", profs["nome"])
grade_titulo = c2.selectbox("Turno / Segmento", grades["titulo"])

prof_id = int(profs.loc[profs["nome"] == prof_nome, "id"].iloc[0])
grade_row = grades.loc[grades["titulo"] == grade_titulo].iloc[0]
grade_id = int(grade_row["id"])
dias = [d.strip() for d in grade_row["dias_semana"].split(",")]

with engine.connect() as conn:
    horarios = pd.read_sql(text("""
        SELECT h.id, h.dia, h.ordem, h.inicio, h.fim
        FROM horarios h
        WHERE h.grade_id = :g
        ORDER BY h.ordem, h.dia
    """), conn, params={"g": grade_id})

if horarios.empty:
    st.info("Esta grade ainda não tem horários criados. "
            "Vá em 'Gerar Grade' e clique em Gerar uma vez para criar.")
    st.stop()

pivot = horarios.pivot(index="ordem", columns="dia", values="id")

pivot.index = [f"{i}ª aula" for i in pivot.index]

with engine.connect() as conn:
    res = conn.execute(text(
        "SELECT horario_id FROM restricoes_professor WHERE professor_id = :p"
    ), {"p": prof_id}).fetchall()
indisponiveis = {r.horario_id for r in res}

df_inicial = pivot.applymap(lambda h_id: h_id in indisponiveis)
df_inicial.columns.name = None

st.subheader(f"Marque com ✓ os horários indisponíveis de {prof_nome}")

editado = st.data_editor(
    df_inicial,
    column_config={
        col: st.column_config.CheckboxColumn(col, default=False)
        for col in df_inicial.columns
    },
    hide_index=False,
    use_container_width=True,
)

if st.button("💾 Salvar disponibilidade", type="primary"):
    horarios_da_grade = set(pivot.values.flatten())
    with engine.begin() as conn:
        for h_id in horarios_da_grade:
            conn.execute(text(
                "DELETE FROM restricoes_professor "
                "WHERE professor_id = :p AND horario_id = :h"
            ), {"p": prof_id, "h": int(h_id)})

        total = 0
        for idx in editado.index:
            for col in editado.columns:
                if editado.loc[idx, col]:
                    h_id = int(pivot.loc[idx, col])
                    conn.execute(text(
                        "INSERT INTO restricoes_professor (professor_id, horario_id) "
                        "VALUES (:p, :h)"
                    ), {"p": prof_id, "h": h_id})
                    total += 1

    st.session_state["msg_disp"] = f"✅ {total} restrições salvas para {prof_nome}."

if "msg_disp" in st.session_state:
    st.success(st.session_state.pop("msg_disp"))
