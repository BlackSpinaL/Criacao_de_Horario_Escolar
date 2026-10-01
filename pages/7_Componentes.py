import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Componentes", page_icon="📚", layout="wide")
st.title("📚 Componentes Curriculares")
st.caption(
    "Disciplinas do colégio. Marque a **mãe** quando for uma disciplina filha "
    "(ex: Ciências/Lab → mãe é Ciências)."
)

engine = get_engine()

# ---------- Mensagens ----------
if "msg_comp" in st.session_state:
    tipo, texto = st.session_state.pop("msg_comp")
    getattr(st, tipo)(texto)

# ---------- Lista para escolher a mãe ----------
with engine.connect() as conn:
    existentes = pd.read_sql(
        text("SELECT nome FROM componentes ORDER BY nome"), conn
    )

opcoes_mae = ["(nenhuma)"] + existentes["nome"].tolist()

# =====================================================================
# ➕ CADASTRO
# =====================================================================
with st.form("novo_comp", clear_on_submit=True):
    c1, c2 = st.columns([3, 2])
    nome = c1.text_input("Nome do componente")
    area = c2.selectbox(
        "Área",
        ["Linguagens", "Matemática", "Ciências", "Humanas",
         "Ensino Religioso", "Outros"],
    )

    c3, c4 = st.columns([2, 2])
    pratica_lab = c3.checkbox("Tem aula prática no laboratório?")
    mae = c4.selectbox(
        "É filha de qual componente? (opcional)",
        opcoes_mae,
        help="Ex: 'Ciências/Lab' é filha de 'Ciências'",
    )

    if st.form_submit_button("➕ Adicionar", type="primary"):
        if not nome.strip():
            st.session_state["msg_comp"] = ("error", "Informe o nome.")
        else:
            try:
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO componentes
                        (nome, area, pratica_lab, agrupa_com)
                        VALUES (:n, :a, :p, :m)
                    """), {
                        "n": nome.strip(),
                        "a": area,
                        "p": pratica_lab,
                        "m": None if mae == "(nenhuma)" else mae,
                    })
                st.session_state["msg_comp"] = (
                    "success", f"✅ '{nome.strip()}' cadastrado!"
                )
            except Exception as e:
                if "unique" in str(e).lower():
                    st.session_state["msg_comp"] = (
                        "warning", f"⚠️ '{nome}' já existe."
                    )
                else:
                    st.session_state["msg_comp"] = ("error", f"Erro: {e}")
            st.rerun()

# =====================================================================
# 📋 LISTA
# =====================================================================
with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT id, nome, area, pratica_lab, agrupa_com
        FROM componentes
        ORDER BY area, nome
    """), conn)

st.subheader(f"Cadastrados ({len(df)})")

if df.empty:
    st.info("Nenhum componente cadastrado ainda.")
    st.stop()

# ---------- Filtro por área ----------
areas = ["Todas"] + sorted(df["area"].dropna().unique().tolist())
filtro_area = st.selectbox("Filtrar por área", areas)
df_view = df if filtro_area == "Todas" else df[df["area"] == filtro_area]

df_edit = df_view.copy()
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
        "nome": st.column_config.TextColumn(
            "Componente", disabled=True, width="large"
        ),
        "area": st.column_config.TextColumn(
            "Área", disabled=True, width="medium"
        ),
        "pratica_lab": st.column_config.CheckboxColumn(
            "Lab?", disabled=True, width="small"
        ),
        "agrupa_com": st.column_config.TextColumn(
            "Filha de", disabled=True, width="medium"
        ),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_comp",
)

# ---------- Barra de ações ----------
marcados = editado[editado["sel"]]
n_marc = len(marcados)
col1, col2, _ = st.columns([2, 1, 4])

if n_marc == 0:
    col1.caption("☝️ Marque componentes na coluna 🗑️ para deletar")
else:
    ids = marcados["id"].astype(int).tolist()
    placeholders = ",".join(str(i) for i in ids)

    with engine.connect() as conn:
        conflitos = pd.read_sql(text(f"""
            SELECT c.nome,
                (SELECT COUNT(*) FROM itens_matriz WHERE componente_id = c.id) AS n_matriz,
                (SELECT COUNT(*) FROM atividades WHERE componente_id = c.id) AS n_atv
            FROM componentes c
            WHERE c.id IN ({placeholders})
        """), conn)
        conflitos = conflitos[
            (conflitos["n_matriz"] > 0) | (conflitos["n_atv"] > 0)
        ]

    if not conflitos.empty:
        col1.warning(f"⚠️ {n_marc} componente(s) com uso")
        st.warning(
            "**Atenção:** componentes em uso:\n\n" +
            "\n".join([
                f"- **{r.nome}** — {r.n_matriz} matriz(es), {r.n_atv} atividade(s)"
                for r in conflitos.itertuples()
            ])
        )
        confirmar = st.checkbox(
            "☑️ Confirmo deletar componentes, itens de matriz e atividades vinculadas"
        )
        if col2.button(
            f"🗑️ Deletar ({n_marc})", type="primary", disabled=not confirmar
        ):
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"DELETE FROM atividades WHERE componente_id IN ({placeholders})"
                    ))
                    conn.execute(text(
                        f"DELETE FROM itens_matriz WHERE componente_id IN ({placeholders})"
                    ))
                    conn.execute(text(
                        f"DELETE FROM componentes WHERE id IN ({placeholders})"
                    ))
                st.session_state["msg_comp"] = (
                    "success", f"🗑️ {n_marc} componente(s) deletado(s)!"
                )
            except Exception as e:
                st.session_state["msg_comp"] = ("error", f"Erro: {e}")
            st.rerun()
    else:
        col1.warning(f"⚠️ {n_marc} componente(s) selecionado(s)")
        if col2.button(f"🗑️ Deletar ({n_marc})", type="primary"):
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"DELETE FROM componentes WHERE id IN ({placeholders})"
                    ))
                st.session_state["msg_comp"] = (
                    "success", f"🗑️ {n_marc} componente(s) deletado(s)!"
                )
            except Exception as e:
                st.session_state["msg_comp"] = ("error", f"Erro: {e}")
            st.rerun()
