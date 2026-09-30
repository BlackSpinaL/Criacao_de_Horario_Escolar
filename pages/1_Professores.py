import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Professores", page_icon="👨‍🏫", layout="wide")
st.title("👨‍🏫 Professores")

engine = get_engine()

# =====================================================================
# Mensagens de feedback (aparecem após rerun)
# =====================================================================
if "msg_prof" in st.session_state:
    tipo, texto = st.session_state.pop("msg_prof")
    getattr(st, tipo)(texto)

# =====================================================================
# ➕ CADASTRO DE PROFESSOR
# =====================================================================
with st.form("novo_prof", clear_on_submit=True):
    c1, c2 = st.columns([4, 1])
    nome = c1.text_input("Nome do professor(a)")
    carga = c2.number_input("Carga máx. (aulas/sem)", 1, 60, 40)

    if st.form_submit_button("➕ Adicionar", type="primary"):
        if not nome.strip():
            st.session_state["msg_prof"] = ("error", "Informe o nome.")
        else:
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        "INSERT INTO professores (nome, carga_max) "
                        "VALUES (:n, :c)"
                    ), {"n": nome.strip(), "c": carga})
                st.session_state["msg_prof"] = (
                    "success", f"✅ {nome.strip()} cadastrado(a)!"
                )
            except Exception as e:
                if "unique" in str(e).lower():
                    st.session_state["msg_prof"] = (
                        "warning",
                        f"⚠️ Já existe um professor com o nome '{nome}'."
                    )
                else:
                    st.session_state["msg_prof"] = ("error", f"Erro: {e}")
        st.rerun()

# =====================================================================
# 📋 LISTA COM MULTI-SELEÇÃO
# =====================================================================
with engine.connect() as conn:
    df = pd.read_sql(text(
        "SELECT id, nome, carga_max FROM professores ORDER BY nome"
    ), conn)

st.subheader(f"Cadastrados ({len(df)})")

if df.empty:
    st.info("Nenhum professor cadastrado ainda. Use o formulário acima.")
    st.stop()

# ---------- DataFrame com checkbox ----------
df_edit = df.copy()
df_edit.insert(0, "sel", False)

editado = st.data_editor(
    df_edit,
    column_config={
        "sel": st.column_config.CheckboxColumn(
            "🗑️",
            help="Marque para deletar",
            default=False,
            width="small",
        ),
        "id": st.column_config.NumberColumn(
            "ID", disabled=True, width="small"
        ),
        "nome": st.column_config.TextColumn(
            "Nome", disabled=True, width="large"
        ),
        "carga_max": st.column_config.NumberColumn(
            "Carga máx.", disabled=True, width="small"
        ),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_profs",
)

# =====================================================================
# 🗑️ BARRA DE AÇÕES
# =====================================================================
marcados = editado[editado["sel"]]
n_marc = len(marcados)

col1, col2, col3 = st.columns([2, 1, 4])

if n_marc == 0:
    col1.caption("☝️ Marque professores na coluna 🗑️ para deletar")
else:
    ids = marcados["id"].astype(int).tolist()
    placeholders = ",".join([str(i) for i in ids])

    # ---------- Verifica se algum tem atividades vinculadas ----------
    with engine.connect() as conn:
        conflitos = pd.read_sql(text(f"""
            SELECT p.id, p.nome, COUNT(a.id) AS n_atividades
            FROM professores p
            LEFT JOIN atividades a ON a.professor_id = p.id
            WHERE p.id IN ({placeholders})
            GROUP BY p.id, p.nome
            HAVING COUNT(a.id) > 0
            ORDER BY p.nome
        """), conn)

    if not conflitos.empty:
        # ---------- CASO COM CONFLITO ----------
        col1.warning(f"⚠️ {n_marc} selecionado(s), mas há aulas atribuídas")

        st.warning(
            "**Atenção:** os professores abaixo têm aulas atribuídas. "
            "Deletá-los removerá **também** essas atribuições:\n\n" +
            "\n".join([
                f"- **{r.nome}** — {r.n_atividades} aula(s) atribuída(s)"
                for r in conflitos.itertuples()
            ])
        )

        confirmar = st.checkbox(
            "☑️ Confirmo que quero deletar o(s) professor(es) **e** suas atribuições"
        )

        if col2.button(
            f"🗑️ Deletar ({n_marc})",
            type="primary",
            disabled=not confirmar,
        ):
            try:
                with engine.begin() as conn:
                    # Primeiro deleta as atribuições (evita FK)
                    conn.execute(text(
                        f"DELETE FROM atividades WHERE professor_id IN ({placeholders})"
                    ))
                    # Depois deleta os professores
                    conn.execute(text(
                        f"DELETE FROM professores WHERE id IN ({placeholders})"
                    ))
                st.session_state["msg_prof"] = (
                    "success",
                    f"🗑️ {n_marc} professor(es) e suas atribuições foram deletados!"
                )
            except Exception as e:
                st.session_state["msg_prof"] = ("error", f"Erro: {e}")
            st.rerun()

    else:
        # ---------- CASO SEM CONFLITO ----------
        col1.warning(f"⚠️ {n_marc} professor(es) selecionado(s)")

        if col2.button(f"🗑️ Deletar ({n_marc})", type="primary"):
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"DELETE FROM professores WHERE id IN ({placeholders})"
                    ))
                st.session_state["msg_prof"] = (
                    "success", f"🗑️ {n_marc} professor(es) deletado(s)!"
                )
            except Exception as e:
                st.session_state["msg_prof"] = ("error", f"Erro: {e}")
            st.rerun()
