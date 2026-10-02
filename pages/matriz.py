import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Matriz Curricular", page_icon="📚", layout="wide")
st.title("📚 Matriz Curricular")
st.caption("Consulte, edite e gerencie a matriz curricular de cada série.")

engine = get_engine()

# ---------- Ano letivo ativo ----------
with engine.connect() as conn:
    ano_id = conn.execute(
        text("SELECT id FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
    ).scalar()
    anos = pd.read_sql(
        text("SELECT id, ano FROM anos_letivos ORDER BY ano DESC"), conn
    )

if ano_id is None:
    st.warning("Rode o seed 2026 primeiro.")
    st.stop()

st.info(f"📅 Editando o ano letivo: **{int(anos.loc[anos['id'] == ano_id, 'ano'].iloc[0])}**")

# ---------- Mensagens ----------
if "msg_matriz" in st.session_state:
    tipo, texto = st.session_state.pop("msg_matriz")
    getattr(st, tipo)(texto)

# ---------- Séries disponíveis ----------
with engine.connect() as conn:
    series = pd.read_sql(text("""
        SELECT DISTINCT serie, segmento FROM matrizes
        WHERE ano_letivo_id = :a ORDER BY segmento, serie
    """), conn, params={"a": ano_id})

if series.empty:
    st.info("Nenhuma matriz cadastrada para este ano.")
    st.stop()

serie_sel = st.selectbox("Série", series["serie"].tolist())

# ---------- Dados da matriz atual ----------
with engine.connect() as conn:
    matriz_row = conn.execute(text(
        "SELECT id FROM matrizes WHERE ano_letivo_id = :a AND serie = :s"
    ), {"a": ano_id, "s": serie_sel}).first()

if matriz_row is None:
    st.warning("Matriz não encontrada para esta série.")
    st.stop()

matriz_id = matriz_row.id

with engine.connect() as conn:
    df_atual = pd.read_sql(text("""
        SELECT im.id AS item_id,
               c.nome AS componente,
               c.area AS area,
               im.aulas_semana AS aulas_sem,
               im.grupo_opcao AS grupo,
               im.turno_extra AS turno_extra
        FROM itens_matriz im
        JOIN componentes c ON c.id = im.componente_id
        WHERE im.matriz_id = :m
        ORDER BY c.area, c.nome
    """), conn, params={"m": matriz_id})

# ---------- Métricas ----------
total_sem = int(df_atual["aulas_sem"].sum()) if not df_atual.empty else 0
c1, c2, c3 = st.columns(3)
c1.metric("Componentes", len(df_atual))
c2.metric("Aulas semanais", total_sem)
c3.metric("Aulas anuais", total_sem * 40)

st.divider()

# =====================================================================
# ✏️ EDITOR
# =====================================================================
st.subheader("✏️ Editar matriz")

if df_atual.empty:
    st.info("A matriz está vazia. Use o formulário abaixo para adicionar componentes.")
else:
    editavel = df_atual[["componente", "area", "aulas_sem", "grupo", "turno_extra"]].copy()
    editavel = editavel.rename(columns={
        "componente": "Componente",
        "area": "Área",
        "aulas_sem": "Aulas/sem",
        "grupo": "Grupo",
        "turno_extra": "Turno extra",
    })

    editado = st.data_editor(
        editavel,
        column_config={
            "Componente": st.column_config.TextColumn(disabled=True, width="large"),
            "Área": st.column_config.TextColumn(disabled=True, width="medium"),
            "Aulas/sem": st.column_config.NumberColumn(
                min_value=0, max_value=20, step=1, width="small"
            ),
            "Grupo": st.column_config.TextColumn(
                help="Ex: IF_ELETIVA (eletiva do itinerário formativo)",
                width="small",
            ),
            "Turno extra": st.column_config.SelectboxColumn(
                options=["", "Manhã", "Tarde"],
                width="small",
            ),
        },
        hide_index=True,
        use_container_width=True,
        key=f"editor_{serie_sel}",
    )

    col_salvar, col_remover, _ = st.columns([1, 1, 3])

    if col_salvar.button("💾 Salvar alterações", type="primary"):
        try:
            with engine.begin() as conn:
                for idx, row in editado.iterrows():
                    item_id = int(df_atual.iloc[idx]["item_id"])
                    conn.execute(text("""
                        UPDATE itens_matriz
                        SET aulas_semana = :a,
                            grupo_opcao = :g,
                            turno_extra = :t
                        WHERE id = :id
                    """), {
                        "a": int(row["Aulas/sem"]),
                        "g": (row["Grupo"] or "").strip() or None,
                        "t": (row["Turno extra"] or "").strip() or None,
                        "id": item_id,
                    })
            st.session_state["msg_matriz"] = (
                "success", f"✅ Matriz de {serie_sel} atualizada!"
            )
            st.rerun()
        except Exception as e:
            st.session_state["msg_matriz"] = ("error", f"Erro: {e}")
            st.rerun()

    # ---------- Remover componente ----------
    remover_opcoes = {int(df_atual.iloc[i]["item_id"]): df_atual.iloc[i]["componente"]
                      for i in range(len(df_atual))}
    comp_remover = col_remover.selectbox(
        "Remover",
        [""] + list(remover_opcoes.keys()),
        format_func=lambda x: remover_opcoes.get(x, "—") if x else "—",
    )
    if comp_remover and st.button("🗑️ Remover componente"):
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM itens_matriz WHERE id = :id"),
                {"id": int(comp_remover)},
            )
        st.session_state["msg_matriz"] = (
            "success", "🗑️ Componente removido da matriz."
        )
        st.rerun()

st.divider()

# =====================================================================
# ➕ ADICIONAR COMPONENTE À MATRIZ
# =====================================================================
st.subheader("➕ Adicionar componente à matriz")

with engine.connect() as conn:
    todos_comps = pd.read_sql(
        text("SELECT id, nome, area FROM componentes ORDER BY area, nome"), conn
    )
    ja_na_matriz = set(df_atual["componente"].tolist())

# Filtra componentes que já estão na matriz
disponiveis = todos_comps[~todos_comps["nome"].isin(ja_na_matriz)]

if disponiveis.empty:
    st.info("Todos os componentes já estão nesta matriz.")
else:
    with st.form("add_comp_matriz", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        comp_nome = c1.selectbox(
            "Componente",
            disponiveis["nome"].tolist(),
        )
        aulas = c2.number_input("Aulas/sem", 1, 20, 1)
        grupo = c3.text_input("Grupo (opcional)", placeholder="IF_ELETIVA")
        turno_extra = c4.selectbox("Turno extra", ["", "Manhã", "Tarde"])

        if st.form_submit_button("➕ Adicionar", type="primary"):
            comp_id = int(
                disponiveis.loc[disponiveis["nome"] == comp_nome, "id"].iloc[0]
            )
            try:
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO itens_matriz
                        (matriz_id, componente_id, aulas_semana,
                         grupo_opcao, turno_extra)
                        VALUES (:m, :c, :a, :g, :t)
                    """), {
                        "m": matriz_id,
                        "c": comp_id,
                        "a": aulas,
                        "g": grupo.strip() or None,
                        "t": turno_extra or None,
                    })
                st.session_state["msg_matriz"] = (
                    "success",
                    f"✅ {comp_nome} adicionado à matriz de {serie_sel}!"
                )
                st.rerun()
            except Exception as e:
                st.session_state["msg_matriz"] = ("error", f"Erro: {e}")
                st.rerun()

st.divider()

# =====================================================================
# 🆕 NOVO COMPONENTE (cadastrar no banco geral)
# =====================================================================
with st.expander("➕ Cadastrar novo componente no banco (aparece em todas as séries)"):
    st.caption(
        "Use isto para componentes que ainda não existem no banco. "
        "Depois de cadastrar aqui, você pode adicioná-lo a qualquer matriz."
    )
    with st.form("novo_comp", clear_on_submit=True):
        c1, c2 = st.columns([3, 2])
        nome_novo = c1.text_input("Nome do componente")
        area_nova = c2.selectbox(
            "Área",
            ["Linguagens", "Matemática", "Ciências", "Humanas",
             "Ensino Religioso", "Outros"],
        )
        if st.form_submit_button("➕ Cadastrar componente"):
            if not nome_novo.strip():
                st.error("Informe o nome.")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(text(
                            "INSERT INTO componentes (nome, area) "
                            "VALUES (:n, :a)"
                        ), {"n": nome_novo.strip(), "a": area_nova})
                    st.session_state["msg_matriz"] = (
                        "success", f"✅ Componente '{nome_novo}' cadastrado!"
                    )
                    st.rerun()
                except Exception as e:
                    st.session_state["msg_matriz"] = ("error", f"Erro: {e}")
                    st.rerun()
