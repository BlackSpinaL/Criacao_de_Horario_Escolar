import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Turmas", page_icon="🏫", layout="wide")
st.title("🏫 Turmas")

engine = get_engine()

# ---------- Ano letivo ----------
with engine.connect() as conn:
    ano_row = conn.execute(
        text("SELECT id, ano FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
    ).first()

if ano_row is None:
    st.warning("Rode o seed 2026 primeiro.")
    st.stop()

ano_id = ano_row.id
st.caption(f"📅 Ano letivo: **{ano_row.ano}**")

with engine.connect() as conn:
    grades = pd.read_sql(text(
        "SELECT id, chave, titulo, turno FROM grades_horarias "
        "WHERE ano_letivo_id = :a ORDER BY titulo"
    ), conn, params={"a": ano_id})

# ---------- Mensagens ----------
if "msg_turma" in st.session_state:
    tipo, texto = st.session_state.pop("msg_turma")
    getattr(st, tipo)(texto)

# =====================================================================
# ➕ CADASTRO
# =====================================================================
with st.form("nova_turma", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
    codigo = c1.text_input("Código", placeholder="11801")
    serie = c2.text_input("Série", placeholder="8º ano")
    grade_id = c3.selectbox(
        "Turno/Segmento",
        grades["id"].tolist(),
        format_func=lambda x: grades.loc[grades["id"] == x, "titulo"].iloc[0],
    )
    alunos = c4.number_input("Alunos", 0, 100, 0, step=1)

    if st.form_submit_button("➕ Adicionar", type="primary"):
        if not codigo.strip() or not serie.strip():
            st.session_state["msg_turma"] = ("error", "Preencha código e série.")
        else:
            grade_row = grades.loc[grades["id"] == grade_id].iloc[0]
            try:
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO turmas
                        (ano_letivo_id, codigo, nome, serie, turno,
                         segmento, grade_horaria_id, alunos)
                        VALUES (:a, :c, :n, :s, :t, :sg, :g, :al)
                    """), {
                        "a": ano_id,
                        "c": codigo.strip(),
                        "n": f"{serie.strip()} ({codigo.strip()})",
                        "s": serie.strip(),
                        "t": grade_row["turno"],
                        "sg": grade_row["chave"],
                        "g": int(grade_id),
                        "al": alunos,
                    })
                st.session_state["msg_turma"] = (
                    "success", f"✅ Turma {codigo.strip()} cadastrada!"
                )
            except Exception as e:
                if "unique" in str(e).lower():
                    st.session_state["msg_turma"] = (
                        "warning", f"⚠️ Código '{codigo}' já existe."
                    )
                else:
                    st.session_state["msg_turma"] = ("error", f"Erro: {e}")
            st.rerun()

# =====================================================================
# 📋 LISTA
# =====================================================================
with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT t.id, t.codigo, t.serie, t.turno, t.segmento, t.alunos,
               g.titulo AS grade
        FROM turmas t
        LEFT JOIN grades_horarias g ON g.id = t.grade_horaria_id
        WHERE t.ano_letivo_id = :a
        ORDER BY t.codigo
    """), conn, params={"a": ano_id})

st.subheader(f"Cadastradas ({len(df)})")

if df.empty:
    st.info("Nenhuma turma cadastrada ainda. Use o formulário acima.")
    st.stop()

df_edit = df.copy()
df_edit.insert(0, "sel", False)

editado = st.data_editor(
    df_edit,
    column_config={
        "sel": st.column_config.CheckboxColumn(
            "🗑️", default=False, width="small"
        ),
        "id": st.column_config.NumberColumn(
            "ID", disabled=True, width="small"
        ),
        "codigo": st.column_config.TextColumn(
            "Código", disabled=True, width="small"
        ),
        "serie": st.column_config.TextColumn(
            "Série", disabled=True, width="medium"
        ),
        "turno": st.column_config.TextColumn(
            "Turno", disabled=True, width="small"
        ),
        "segmento": st.column_config.TextColumn(
            "Segmento", disabled=True, width="small"
        ),
        "grade": st.column_config.TextColumn(
            "Grade", disabled=True, width="medium"
        ),
        "alunos": st.column_config.NumberColumn(
            "Alunos", disabled=True, width="small"
        ),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_turmas",
)

# ---------- Barra de ações ----------
marcados = editado[editado["sel"]]
n_marc = len(marcados)
col1, col2, _ = st.columns([2, 1, 4])

if n_marc == 0:
    col1.caption("☝️ Marque turmas na coluna 🗑️ para deletar")
else:
    ids = marcados["id"].astype(int).tolist()
    placeholders = ",".join(str(i) for i in ids)

    with engine.connect() as conn:
        conflitos = pd.read_sql(text(f"""
            SELECT t.nome, COUNT(a.id) AS n_atv
            FROM turmas t
            LEFT JOIN atividades a ON a.turma_id = t.id
            WHERE t.id IN ({placeholders})
            GROUP BY t.id, t.nome
            HAVING COUNT(a.id) > 0
        """), conn)

    if not conflitos.empty:
        col1.warning(f"⚠️ {n_marc} turma(s) com aulas atribuídas")
        st.warning(
            "**Atenção:** turmas com atividades vinculadas:\n\n" +
            "\n".join([
                f"- **{r.nome}** — {r.n_atv} atividade(s)"
                for r in conflitos.itertuples()
            ])
        )
        confirmar = st.checkbox(
            "☑️ Confirmo deletar turma(s) **e** suas atividades"
        )
        if col2.button(
            f"🗑️ Deletar ({n_marc})", type="primary", disabled=not confirmar
        ):
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"DELETE FROM atividades WHERE turma_id IN ({placeholders})"
                    ))
                    conn.execute(text(
                        f"DELETE FROM turmas WHERE id IN ({placeholders})"
                    ))
                st.session_state["msg_turma"] = (
                    "success", f"🗑️ {n_marc} turma(s) deletada(s)!"
                )
            except Exception as e:
                st.session_state["msg_turma"] = ("error", f"Erro: {e}")
            st.rerun()
    else:
        col1.warning(f"⚠️ {n_marc} turma(s) selecionada(s)")
        if col2.button(f"🗑️ Deletar ({n_marc})", type="primary"):
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"DELETE FROM turmas WHERE id IN ({placeholders})"
                    ))
                st.session_state["msg_turma"] = (
                    "success", f"🗑️ {n_marc} turma(s) deletada(s)!"
                )
            except Exception as e:
                st.session_state["msg_turma"] = ("error", f"Erro: {e}")
            st.rerun()
