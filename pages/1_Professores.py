import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Professores", page_icon="👨‍🏫", layout="wide")
st.title("👨‍🏫 Professores")

engine = get_engine()

# ---------- Mensagens ----------
if "msg_prof" in st.session_state:
    tipo, texto = st.session_state.pop("msg_prof")
    getattr(st, tipo)(texto)

# =====================================================================
# ➕ CADASTRO
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
                        "warning", f"⚠️ Já existe um professor com o nome '{nome}'."
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

# ---------- Prepara DataFrame com checkbox ----------
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

# ---------- Barra de ações ----------
marcados = editado[editado["sel"]]
n_marc = len(marcados)

col1, col2, col3 = st.columns([2, 1, 4])

if n_marc == 0:
    col1.caption("☝️ Marque professores na coluna 🗑️ para deletar")
else:
    col1.warning(f"⚠️ {n_marc} professor(es) selecionado(s)")

    if col2.button(f"🗑️ Deletar ({n_marc})", type="primary"):
        ids = marcados["id"].astype(int).tolist()
        nomes = marcados["nome"].tolist()
        try:
            with engine.begin() as conn:
                for id_prof in ids:
                    conn.execute(
                        text("DELETE FROM professores WHERE id = :id"),
                        {"id": id_prof},
                    )
            if n_marc == 1:
                st.session_state["msg_prof"] = (
                    "success", f"🗑️ '{nomes[0]}' deletado(a)!"
                )
            else:
                st.session_state["msg_prof"] = (
                    "success", f"🗑️ {n_marc} professores deletados!"
                )
        except Exception as e:
            st.session_state["msg_prof"] = ("error", f"Erro: {e}")
        st.rerun()
