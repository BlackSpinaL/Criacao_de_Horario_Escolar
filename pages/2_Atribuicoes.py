import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Atribuições", page_icon="🔗", layout="wide")
st.title("🔗 Atribuições — Professor × Componente × Turma")

engine = get_engine()

# ---------- Ano letivo ----------
with engine.connect() as conn:
    ano_id = conn.execute(
        text("SELECT id FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
    ).scalar()

if ano_id is None:
    st.warning("Rode o seed 2026 na página inicial primeiro.")
    st.stop()

# ---------- Turmas ----------
with engine.connect() as conn:
    turmas = pd.read_sql(text(
        "SELECT id, codigo, nome, serie FROM turmas "
        "WHERE ano_letivo_id = :a ORDER BY codigo"
    ), conn, params={"a": ano_id})

if turmas.empty:
    st.warning("Nenhuma turma cadastrada.")
    st.stop()

turma_sel = st.selectbox(
    "Turma",
    turmas["id"].tolist(),
    format_func=lambda x: turmas.loc[turmas["id"] == x, "nome"].iloc[0],
)
turma_row = turmas.loc[turmas["id"] == turma_sel].iloc[0]

st.divider()

# =====================================================================
# 📊 TABELA COMPARATIVA: MATRIZ × ATRIBUÍDO
# =====================================================================
st.subheader(f"📊 Matriz × Atribuído — {turma_row['nome']}")

with engine.connect() as conn:
    comparativo = pd.read_sql(text("""
        SELECT
            c.id AS componente_id,
            c.nome AS componente,
            im.aulas_semana AS matriz_semana,
            im.aulas_semana * 40 AS matriz_anual,
            COALESCE(
                (SELECT SUM(a.aulas_semana)
                 FROM atividades a
                 WHERE a.turma_id = :t AND a.componente_id = c.id),
                0
            ) AS atribuida_semana,
            COALESCE(
                (SELECT STRING_AGG(p.nome, ', ' ORDER BY p.nome)
                 FROM atividades a
                 JOIN professores p ON p.id = a.professor_id
                 WHERE a.turma_id = :t AND a.componente_id = c.id),
                '—'
            ) AS professores
        FROM matrizes m
        JOIN itens_matriz im ON im.matriz_id = m.id
        JOIN componentes c   ON c.id = im.componente_id
        WHERE m.ano_letivo_id = :a AND m.serie = :s
        ORDER BY c.nome
    """), conn, params={"a": ano_id, "t": int(turma_sel), "s": turma_row["serie"]})

if comparativo.empty:
    st.info(f"Não há matriz cadastrada para a série '{turma_row['serie']}'.")
    st.stop()

# ---------- Calcula situação ----------
def calcular_situacao(row):
    atrib = int(row["atribuida_semana"])
    matriz = int(row["matriz_semana"])
    if atrib == matriz:
        return "✅ OK"
    elif atrib == 0:
        return "❌ Não atribuído"
    elif atrib < matriz:
        return f"⚠️ Faltam {matriz - atrib}"
    else:
        return f"🟡 Excedem {atrib - matriz}"

comparativo["situacao"] = comparativo.apply(calcular_situacao, axis=1)
comparativo["atribuida_anual"] = comparativo["atribuida_semana"] * 40

# ---------- Cor por linha ----------
def colorir(row):
    s = row["Situação"]
    if s.startswith("✅"):
        return ["background-color: #d4edda"] * len(row)
    elif s.startswith("⚠️") or s.startswith("❌"):
        return ["background-color: #f8d7da"] * len(row)
    elif s.startswith("🟡"):
        return ["background-color: #fff3cd"] * len(row)
    return [""] * len(row)

# ---------- Renomeia colunas para exibição ----------
df_exibir = comparativo[[
    "componente", "matriz_semana", "matriz_anual",
    "atribuida_semana", "atribuida_anual",
    "professores", "situacao"
]].rename(columns={
    "componente": "Componente",
    "matriz_semana": "Matriz (aulas/sem)",
    "matriz_anual": "Matriz (aulas/ano)",
    "atribuida_semana": "Atribuído (aulas/sem)",
    "atribuida_anual": "Atribuído (aulas/ano)",
    "professores": "Professor(es)",
    "situacao": "Situação",
})

styled = df_exibir.style.apply(colorir, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True)

# ---------- Estatísticas ----------
total_matriz = int(comparativo["matriz_semana"].sum())
total_atrib = int(comparativo["atribuida_semana"].sum())
c1, c2, c3 = st.columns(3)
c1.metric("Aulas previstas na matriz", total_matriz)
c2.metric("Aulas atribuídas", total_atrib)
delta = total_atrib - total_matriz
c3.metric(
    "Diferença",
    delta,
    delta=f"{delta:+d}" if delta != 0 else None,
    delta_color="off" if delta == 0 else ("normal" if delta < 0 else "inverse"),
)

st.divider()

# =====================================================================
# ✏️ EDITOR INLINE
# =====================================================================
st.subheader("✏️ Ajustar aulas atribuídas")

with st.expander("Clique para editar", expanded=False):
    st.caption(
        "Edite a coluna 'Aulas/sem' para atualizar a quantidade de aulas "
        "atribuídas de cada componente. Se não houver professor vinculado, "
        "use o formulário abaixo."
    )
    editavel = comparativo[["componente", "professores", "atribuida_semana"]].copy()
    editavel = editavel.rename(columns={
        "componente": "Componente",
        "professores": "Professor(es)",
        "atribuida_semana": "Aulas/sem",
    })

    editado = st.data_editor(
        editavel,
        column_config={
            "Componente": st.column_config.TextColumn(disabled=True),
            "Professor(es)": st.column_config.TextColumn(disabled=True),
            "Aulas/sem": st.column_config.NumberColumn(min_value=0, max_value=20),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_inline",
    )

    if st.button("💾 Salvar alterações", type="primary"):
        try:
            with engine.begin() as conn:
                for idx, row in editado.iterrows():
                    comp_id = int(comparativo.iloc[idx]["componente_id"])
                    nova_qtd = int(row["Aulas/sem"])

                    existente = conn.execute(text(
                        "SELECT id FROM atividades "
                        "WHERE turma_id = :t AND componente_id = :c"
                    ), {"t": int(turma_sel), "c": comp_id}).first()

                    if nova_qtd == 0 and existente:
                        conn.execute(text(
                            "DELETE FROM atividades WHERE id = :id"
                        ), {"id": existente.id})
                    elif nova_qtd > 0 and existente:
                        conn.execute(text(
                            "UPDATE atividades SET aulas_semana = :n "
                            "WHERE id = :id"
                        ), {"n": nova_qtd, "id": existente.id})

            st.success("Alterações salvas!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

st.divider()

# =====================================================================
# ➕ CADASTRO
# =====================================================================
st.subheader("➕ Nova atribuição")

with engine.connect() as conn:
    profs = pd.read_sql(
        text("SELECT id, nome FROM professores ORDER BY nome"), conn
    )
    comps_faltantes = comparativo[comparativo["atribuida_semana"] == 0]
    comps_opcoes = comps_faltantes[["componente_id", "componente"]].copy()

if profs.empty:
    st.warning("Cadastre professores primeiro.")
    st.stop()

if comps_opcoes.empty:
    st.success(f"✅ A matriz de {turma_row['nome']} já está totalmente atribuída!")
else:
    with st.form("nova_atv", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 3, 1])
        prof_nome = c1.selectbox("Professor", profs["nome"])
        comp_nome = c2.selectbox("Componente pendente", comps_opcoes["componente"])
        aulas = c3.number_input("Aulas/sem", 1, 20, 1)

        submit = st.form_submit_button("➕ Adicionar", type="primary")

    if submit:
        prof_id = int(profs.loc[profs["nome"] == prof_nome, "id"].iloc[0])
        comp_id = int(comps_opcoes.loc[
            comps_opcoes["componente"] == comp_nome, "componente_id"
        ].iloc[0])

        matriz_qtd = int(comparativo.loc[
            comparativo["componente"] == comp_nome, "matriz_semana"
        ].iloc[0])

        if aulas > matriz_qtd:
            st.warning(
                f"⚠️ A matriz pede apenas {matriz_qtd} aulas/semana de "
                f"{comp_nome}. Você cadastrou {aulas}."
            )
        else:
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        "INSERT INTO atividades (ano_letivo_id, professor_id, "
                        "componente_id, turma_id, aulas_semana) "
                        "VALUES (:a, :p, :c, :t, :n)"
                    ), {"a": ano_id, "p": prof_id, "c": comp_id,
                        "t": int(turma_sel), "n": aulas})
                st.success(
                    f"✅ {prof_nome} → {comp_nome} → {turma_row['nome']}"
                )
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

# ---------- Lista de atribuições atuais ----------
with engine.connect() as conn:
    atuais = pd.read_sql(text("""
        SELECT a.id, p.nome AS professor, c.nome AS componente, a.aulas_semana
        FROM atividades a
        JOIN professores p ON p.id = a.professor_id
        JOIN componentes c ON c.id = a.componente_id
        WHERE a.turma_id = :t
        ORDER BY c.nome, p.nome
    """), conn, params={"t": int(turma_sel)})

st.subheader(f"Atribuições ativas em {turma_row['nome']} ({len(atuais)})")
if atuais.empty:
    st.info("Nenhuma atribuição ainda para esta turma.")
else:
    st.dataframe(atuais, use_container_width=True, hide_index=True)

    remover = st.selectbox("Remover ID", [""] + atuais["id"].tolist())
    if remover and st.button("🗑️ Remover"):
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM atividades WHERE id = :id"),
                {"id": int(remover)},
            )
        st.rerun()
