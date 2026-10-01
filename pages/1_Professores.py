import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Professores", page_icon="👨‍🏫", layout="wide")
st.title("👨‍🏫 Professores")
st.caption("Cadastre apenas o nome. O sistema calcula automaticamente o total de aulas.")

engine = get_engine()

if "msg_prof" in st.session_state:
    tipo, texto = st.session_state.pop("msg_prof")
    getattr(st, tipo)(texto)

# =====================================================================
# ➕ CADASTRO (só nome)
# =====================================================================
with st.form("novo_prof", clear_on_submit=True):
    c1, c2 = st.columns([5, 1])
    nome = c1.text_input("Nome do professor(a)")
    submit = c2.form_submit_button("➕ Adicionar", type="primary")

if submit:
    if not nome.strip():
        st.session_state["msg_prof"] = ("error", "Informe o nome.")
    else:
        try:
            with engine.begin() as conn:
                conn.execute(text(
                    "INSERT INTO professores (nome, carga_max) VALUES (:n, 0)"
                ), {"n": nome.strip()})
            st.session_state["msg_prof"] = (
                "success", f"✅ {nome.strip()} cadastrado(a)!"
            )
        except Exception as e:
            if "unique" in str(e).lower():
                st.session_state["msg_prof"] = (
                    "warning", f"⚠️ Já existe '{nome}'."
                )
            else:
                st.session_state["msg_prof"] = ("error", f"Erro: {e}")
        st.rerun()

# =====================================================================
# 📋 LISTA
# =====================================================================
with engine.connect() as conn:
    ano_id = conn.execute(
        text("SELECT id FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
    ).scalar()

    if ano_id is None:
        st.warning("Rode o seed 2026 primeiro.")
        st.stop()

    df = pd.read_sql(text("""
        SELECT
            p.id,
            p.nome,
            COALESCE(
                (SELECT SUM(a.aulas_semana) FROM atividades a
                 WHERE a.professor_id = p.id AND a.ano_letivo_id = :ano),
                0
            ) AS total_semanal,
            COALESCE(
                (SELECT COUNT(DISTINCT a.turma_id) FROM atividades a
                 WHERE a.professor_id = p.id AND a.ano_letivo_id = :ano),
                0
            ) AS num_turmas,
            COALESCE(
                (SELECT STRING_AGG(DISTINCT c.nome, ', ')
                 FROM atividades a
                 JOIN componentes c ON c.id = a.componente_id
                 WHERE a.professor_id = p.id AND a.ano_letivo_id = :ano),
                '—'
            ) AS disciplinas
        FROM professores p
        ORDER BY p.nome
    """), conn, params={"ano": ano_id})

df["total_anual"] = df["total_semanal"] * 40

st.subheader(f"Cadastrados ({len(df)})")

if df.empty:
    st.info("Nenhum professor cadastrado ainda.")
    st.stop()

# =====================================================================
# 🔎 FILTROS
# =====================================================================
col_f1, col_f2, col_f3 = st.columns([2, 2, 1])

with col_f1:
    busca = st.text_input("🔍 Buscar por nome", placeholder="Digite parte do nome...")

# Extrai disciplinas únicas para filtro
todas_disc = set()
for d in df["disciplinas"].dropna():
    if d and d != "—":
        for item in d.split(", "):
            todas_disc.add(item.strip())
lista_disc = ["(todas)"] + sorted(todas_disc)

with col_f2:
    filtro_disc = st.selectbox("Filtrar por disciplina", lista_disc)

with col_f3:
    st.write("")
    st.write("")

# Aplica filtros
df_filt = df.copy()
if busca:
    df_filt = df_filt[df_filt["nome"].str.contains(busca, case=False, na=False)]
if filtro_disc != "(todas)":
    df_filt = df_filt[df_filt["disciplinas"].str.contains(filtro_disc, na=False)]

# =====================================================================
# 📊 TABELA
# =====================================================================
df_view = df_filt[[
    "id", "nome", "total_semanal", "total_anual",
    "num_turmas", "disciplinas"
]].rename(columns={
    "id": "ID",
    "nome": "Nome",
    "total_semanal": "Aulas/sem",
    "total_anual": "Aulas/ano",
    "num_turmas": "Turmas",
    "disciplinas": "Disciplinas",
})

df_view.insert(0, "🗑️", False)

editado = st.data_editor(
    df_view,
    column_config={
        "🗑️": st.column_config.CheckboxColumn(
            "🗑️", default=False, width="small"
        ),
        "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
        "Nome": st.column_config.TextColumn("Nome", disabled=True, width="large"),
        "Aulas/sem": st.column_config.NumberColumn(
            "Aulas/sem", disabled=True, width="small"
        ),
        "Aulas/ano": st.column_config.NumberColumn(
            "Aulas/ano", disabled=True, width="small"
        ),
        "Turmas": st.column_config.NumberColumn(
            "Turmas", disabled=True, width="small"
        ),
        "Disciplinas": st.column_config.TextColumn(
            "Disciplinas", disabled=True, width="large"
        ),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_profs",
)

# Rodapé com totais
total_sem = int(df_filt["total_semanal"].sum())
st.caption(
    f"📊 **Exibindo {len(df_filt)} de {len(df)} professores** · "
    f"{total_sem} aulas/semana · {total_sem * 40} aulas/ano"
)

# =====================================================================
# 📥 EXPORTAR CSV
# =====================================================================
col_exp1, col_exp2, _ = st.columns([1, 1, 3])
csv = df_filt[[
    "nome", "total_semanal", "total_anual", "num_turmas", "disciplinas"
]].rename(columns={
    "nome": "Professor",
    "total_semanal": "Aulas semanais",
    "total_anual": "Aulas anuais",
    "num_turmas": "Turmas",
    "disciplinas": "Disciplinas",
}).to_csv(index=False).encode("utf-8")

col_exp1.download_button(
    "⬇️ Exportar CSV",
    csv,
    "professores.csv",
    "text/csv",
    use_container_width=True,
)

# =====================================================================
# 👁️ DETALHES DO PROFESSOR
# =====================================================================
st.divider()
st.subheader("👁️ Detalhes do Professor")

if df.empty:
    st.info("Nenhum professor cadastrado ainda.")
else:
    prof_sel = st.selectbox(
        "Escolha um professor para ver os detalhes",
        df["nome"].tolist(),
        key="detalhe_prof",
    )
    prof_id = int(df.loc[df["nome"] == prof_sel, "id"].iloc[0])
    prof_dados = df.loc[df["id"] == prof_id].iloc[0]

    # Cards resumo
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aulas/semana", int(prof_dados["total_semanal"]))
    c2.metric("Aulas/ano", int(prof_dados["total_anual"]))
    c3.metric("Turmas", int(prof_dados["num_turmas"]))
    c4.metric(
        "Disciplinas",
        len([d for d in str(prof_dados["disciplinas"]).split(",") if d.strip() and d.strip() != "—"])
    )

    # Tabela de atribuições detalhadas
    with engine.connect() as conn:
        detalhes = pd.read_sql(text("""
            SELECT
                t.codigo AS "Turma",
                t.serie AS "Série",
                t.turno AS "Turno",
                c.nome AS "Disciplina",
                a.aulas_semana AS "Aulas/sem",
                a.aulas_semana * 40 AS "Aulas/ano"
            FROM atividades a
            JOIN turmas t ON t.id = a.turma_id
            JOIN componentes c ON c.id = a.componente_id
            WHERE a.professor_id = :p AND a.ano_letivo_id = :ano
            ORDER BY t.codigo, c.nome
        """), conn, params={"p": prof_id, "ano": ano_id})

    if detalhes.empty:
        st.info(f"ℹ️ **{prof_sel}** ainda não tem aulas atribuídas.")
    else:
        st.markdown(f"**Aulas atribuídas a {prof_sel}:**")
        st.dataframe(detalhes, use_container_width=True, hide_index=True)

# =====================================================================
# 🗑️ BARRA DE AÇÕES
# =====================================================================
marcados = editado[editado["🗑️"]]
n_marc = len(marcados)
col1, col2, col3 = st.columns([2, 1, 4])

if n_marc == 0:
    col1.caption("☝️ Marque professores na coluna 🗑️ para deletar")
else:
    ids = marcados["ID"].astype(int).tolist()
    placeholders = ",".join(str(i) for i in ids)

    with engine.connect() as conn:
        conflitos = pd.read_sql(text(f"""
            SELECT p.nome, COUNT(a.id) AS n_atv
            FROM professores p
            LEFT JOIN atividades a ON a.professor_id = p.id
            WHERE p.id IN ({placeholders})
            GROUP BY p.id, p.nome
            HAVING COUNT(a.id) > 0
        """), conn)

    if not conflitos.empty:
        col1.warning(f"⚠️ {n_marc} selecionado(s) com aulas atribuídas")
        st.warning(
            "**Atenção:** estes professores têm aulas atribuídas:\n\n" +
            "\n".join([
                f"- **{r.nome}** — {r.n_atv} aula(s)"
                for r in conflitos.itertuples()
            ])
        )
        confirmar = st.checkbox(
            "☑️ Confirmo deletar **e** as atribuições vinculadas"
        )
        if col2.button(
            f"🗑️ Deletar ({n_marc})",
            type="primary",
            disabled=not confirmar,
        ):
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"DELETE FROM atividades WHERE professor_id IN ({placeholders})"
                    ))
                    conn.execute(text(
                        f"DELETE FROM professores WHERE id IN ({placeholders})"
                    ))
                st.session_state["msg_prof"] = (
                    "success", f"🗑️ {n_marc} professor(es) deletado(s)!"
                )
            except Exception as e:
                st.session_state["msg_prof"] = ("error", f"Erro: {e}")
            st.rerun()
    else:
        col1.warning(f"⚠️ {n_marc} selecionado(s)")
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
