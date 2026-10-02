import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Componentes", page_icon="📚", layout="wide")
st.title("📚 Componentes Curriculares")
st.caption("Disciplinas do colégio. Marque a **mãe** quando for uma disciplina filha.")

engine = get_engine()

if "msg_comp" in st.session_state:
    tipo, texto = st.session_state.pop("msg_comp")
    getattr(st, tipo)(texto)

# =====================================================================
# ➕ CADASTRO
# =====================================================================
with engine.connect() as conn:
    existentes = pd.read_sql(
        text("SELECT nome FROM componentes ORDER BY nome"), conn
    )
opcoes_mae = ["(nenhuma)"] + existentes["nome"].tolist()

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
                        "n": nome.strip(), "a": area, "p": pratica_lab,
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
        SELECT
            c.id, c.nome, c.area, c.pratica_lab, c.agrupa_com,
            COALESCE(
                (SELECT COUNT(*) FROM itens_matriz im
                 WHERE im.componente_id = c.id),
                0
            ) AS em_matrizes,
            COALESCE(
                (SELECT COUNT(*) FROM atividades a
                 WHERE a.componente_id = c.id),
                0
            ) AS em_atividades
        FROM componentes c
        ORDER BY c.area, c.nome
    """), conn)

st.subheader(f"Cadastrados ({len(df)})")

if df.empty:
    st.info("Nenhum componente cadastrado ainda.")
    st.stop()

# =====================================================================
# 🔎 FILTROS
# =====================================================================
col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
with col_f1:
    busca = st.text_input("🔍 Buscar por nome", placeholder="Ex: Matemática")
with col_f2:
    areas = ["(todas)"] + sorted(df["area"].dropna().unique().tolist())
    filtro_area = st.selectbox("Filtrar por área", areas)
with col_f3:
    filtro_lab = st.selectbox(
        "Prática de lab?",
        ["(todos)", "Só com lab", "Só sem lab"],
    )

df_filt = df.copy()
if busca:
    df_filt = df_filt[df_filt["nome"].str.contains(busca, case=False, na=False)]
if filtro_area != "(todas)":
    df_filt = df_filt[df_filt["area"] == filtro_area]
if filtro_lab == "Só com lab":
    df_filt = df_filt[df_filt["pratica_lab"] == True]
elif filtro_lab == "Só sem lab":
    df_filt = df_filt[df_filt["pratica_lab"] == False]

# =====================================================================
# 📊 TABELA
# =====================================================================
df_view = df_filt[[
    "id", "nome", "area", "pratica_lab", "agrupa_com",
    "em_matrizes", "em_atividades"
]].rename(columns={
    "id": "ID", "nome": "Componente", "area": "Área",
    "pratica_lab": "Lab?", "agrupa_com": "Filha de",
    "em_matrizes": "Matrizes", "em_atividades": "Aulas",
})
df_view.insert(0, "🗑️", False)

editado = st.data_editor(
    df_view,
    column_config={
        "🗑️": st.column_config.CheckboxColumn("🗑️", default=False, width="small"),
        "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
        "Componente": st.column_config.TextColumn("Componente", disabled=True, width="large"),
        "Área": st.column_config.TextColumn("Área", disabled=True, width="medium"),
        "Lab?": st.column_config.CheckboxColumn("Lab?", disabled=True, width="small"),
        "Filha de": st.column_config.TextColumn("Filha de", disabled=True, width="medium"),
        "Matrizes": st.column_config.NumberColumn("Matrizes", disabled=True, width="small"),
        "Aulas": st.column_config.NumberColumn("Aulas", disabled=True, width="small"),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_comp",
)

st.caption(f"📊 **Exibindo {len(df_filt)} de {len(df)} componentes**")

# =====================================================================
# 📥 EXPORTAR CSV
# =====================================================================
csv = df_filt[[
    "nome", "area", "pratica_lab", "agrupa_com"
]].rename(columns={
    "nome": "Componente", "area": "Área",
    "pratica_lab": "Prática no lab?", "agrupa_com": "Filha de",
}).to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Exportar CSV", csv, "componentes.csv", "text/csv",
)

# =====================================================================
# ✏️ EDITAR COMPONENTE
# =====================================================================
st.divider()
st.subheader("✏️ Editar componente")

with st.expander("Clique para editar", expanded=False):
    opcoes = df["id"].tolist()
    comp_edit_sel = st.selectbox(
        "Escolha o componente",
        opcoes,
        format_func=lambda x: df.loc[df["id"] == x, "nome"].iloc[0],
        key="comp_edit_sel",
    )

    comp_atual = df.loc[df["id"] == comp_edit_sel].iloc[0]

    # Descobre índice da mãe atual
    if comp_atual["agrupa_com"] and comp_atual["agrupa_com"] in opcoes_mae:
        idx_mae = opcoes_mae.index(comp_atual["agrupa_com"])
    else:
        idx_mae = 0

    idx_area = ["Linguagens", "Matemática", "Ciências", "Humanas",
                "Ensino Religioso", "Outros"].index(comp_atual["area"]) \
        if comp_atual["area"] in ["Linguagens", "Matemática", "Ciências",
                                   "Humanas", "Ensino Religioso", "Outros"] else 5

    with st.form("form_editar_comp"):
        c1, c2 = st.columns([3, 2])
        novo_nome = c1.text_input("Nome", value=comp_atual["nome"])
        nova_area = c2.selectbox(
            "Área",
            ["Linguagens", "Matemática", "Ciências", "Humanas",
             "Ensino Religioso", "Outros"],
            index=idx_area,
        )
        c3, c4 = st.columns([2, 2])
        novo_lab = c3.checkbox(
            "Tem prática no laboratório?",
            value=bool(comp_atual["pratica_lab"]),
        )
        nova_mae = c4.selectbox(
            "É filha de qual componente?",
            opcoes_mae,
            index=idx_mae,
        )

        if st.form_submit_button("💾 Salvar alterações", type="primary"):
            if not novo_nome.strip():
                st.error("Informe o nome.")
            elif nova_mae == novo_nome.strip():
                st.error("Um componente não pode ser filho dele mesmo.")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("""
                            UPDATE componentes
                            SET nome = :n,
                                area = :a,
                                pratica_lab = :p,
                                agrupa_com = :m
                            WHERE id = :id
                        """), {
                            "n": novo_nome.strip(),
                            "a": nova_area,
                            "p": novo_lab,
                            "m": None if nova_mae == "(nenhuma)" else nova_mae,
                            "id": int(comp_edit_sel),
                        })
                    st.session_state["msg_comp"] = (
                        "success",
                        f"✅ Componente '{novo_nome.strip()}' atualizado!"
                    )
                    st.rerun()
                except Exception as e:
                    if "unique" in str(e).lower():
                        st.error(f"⚠️ Já existe um componente com o nome '{novo_nome}'.")
                    else:
                        st.error(f"Erro: {e}")

# =====================================================================
# 👁️ DETALHES DO COMPONENTE
# =====================================================================
st.divider()
st.subheader("👁️ Detalhes do Componente")

comp_sel = st.selectbox(
    "Escolha um componente",
    df["id"].tolist(),
    format_func=lambda x: df.loc[df["id"] == x, "nome"].iloc[0],
    key="detalhe_comp",
)

comp_dados = df.loc[df["id"] == comp_sel].iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric("Área", comp_dados["area"] or "—")
c2.metric("Em matrizes", int(comp_dados["em_matrizes"]))
c3.metric("Aulas atribuídas", int(comp_dados["em_atividades"]))

with engine.connect() as conn:
    por_serie = pd.read_sql(text("""
        SELECT
            m.serie AS "Série",
            im.aulas_semana AS "Aulas/sem",
            im.aulas_semana * 40 AS "Aulas/ano"
        FROM itens_matriz im
        JOIN matrizes m ON m.id = im.matriz_id
        WHERE im.componente_id = :c
        ORDER BY m.serie
    """), conn, params={"c": int(comp_sel)})

if por_serie.empty:
    st.info("ℹ️ Este componente não está em nenhuma matriz.")
else:
    st.markdown("**Onde aparece (nas matrizes):**")
    st.dataframe(por_serie, use_container_width=True, hide_index=True)

# =====================================================================
# 🗑️ BARRA DE AÇÕES
# =====================================================================
marcados = editado[editado["🗑️"]]
n_marc = len(marcados)
col1, col2, _ = st.columns([2, 1, 4])

if n_marc == 0:
    col1.caption("☝️ Marque componentes na coluna 🗑️ para deletar")
else:
    ids = marcados["ID"].astype(int).tolist()
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
        col1.warning(f"⚠️ {n_marc} componente(s) em uso")
        st.warning(
            "**Atenção:** componentes em uso:\n\n" +
            "\n".join([
                f"- **{r.nome}** — {r.n_matriz} matriz(es), {r.n_atv} atividade(s)"
                for r in conflitos.itertuples()
            ])
        )
        confirmar = st.checkbox(
            "☑️ Confirmo deletar componentes, itens de matriz e atividades"
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
