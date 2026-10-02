import streamlit as st
import pandas as pd
import re
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Professores", page_icon="👨‍🏫", layout="wide")
st.title("👨‍🏫 Professores")
st.caption("Cadastre o nome completo e o Nº PM. O sistema calcula automaticamente o total de aulas.")

engine = get_engine()

# =====================================================================
# Mensagens de feedback
# =====================================================================
if "msg_prof" in st.session_state:
    tipo, texto = st.session_state.pop("msg_prof")
    getattr(st, tipo)(texto)

# =====================================================================
# Validação do Nº PM
# =====================================================================
def validar_numero_pm(num):
    """Aceita 123456-7, 1234567 ou 123.456-7 (com pontos opcionais)."""
    if not num:
        return None
    limpo = re.sub(r"[^\d-]", "", num)
    padrao = re.match(r"^\d{6}-?\d$", limpo)
    if not padrao:
        return None
    return limpo

# =====================================================================
# ➕ CADASTRO
# =====================================================================
with st.form("novo_prof", clear_on_submit=True):
    c1, c2 = st.columns([3, 1])
    nome = c1.text_input("Nome completo do professor(a)")
    numero_pm = c2.text_input("Nº PM", placeholder="000000-0")

    submit = st.form_submit_button("➕ Adicionar", type="primary")

if submit:
    nome_limpo = nome.strip()
    num_pm = validar_numero_pm(numero_pm.strip()) if numero_pm.strip() else None

    if not nome_limpo:
        st.session_state["msg_prof"] = ("error", "Informe o nome completo.")
    elif numero_pm.strip() and num_pm is None:
        st.session_state["msg_prof"] = (
            "error",
            "Nº PM inválido. Use o formato **000000-0** (6 dígitos + hífen + 1 dígito)."
        )
    else:
        try:
            with engine.begin() as conn:
                conn.execute(text(
                    "INSERT INTO professores (nome, numero_pm, carga_max) "
                    "VALUES (:n, :pm, 0)"
                ), {"n": nome_limpo, "pm": num_pm})
            msg_extra = f" (Nº PM {num_pm})" if num_pm else ""
            st.session_state["msg_prof"] = (
                "success", f"✅ {nome_limpo}{msg_extra} cadastrado(a)!"
            )
        except Exception as e:
            erro = str(e).lower()
            if "idx_professores_numero_pm" in erro or "numero_pm" in erro:
                st.session_state["msg_prof"] = (
                    "warning",
                    f"⚠️ Já existe um professor com o Nº PM {num_pm}."
                )
            elif "unique" in erro:
                st.session_state["msg_prof"] = (
                    "warning", f"⚠️ Já existe um professor com o nome '{nome_limpo}'."
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
            p.numero_pm,
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
df["numero_pm"] = df["numero_pm"].fillna("—")

st.subheader(f"Cadastrados ({len(df)})")

if df.empty:
    st.info("Nenhum professor cadastrado ainda.")
    st.stop()

# =====================================================================
# 🔎 FILTROS
# =====================================================================
col_f1, col_f2, col_f3 = st.columns([2, 2, 1])

with col_f1:
    busca = st.text_input("🔍 Buscar por nome ou Nº PM",
                          placeholder="Ex: João ou 123456-7")

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

df_filt = df.copy()
if busca:
    df_filt = df_filt[
        df_filt["nome"].str.contains(busca, case=False, na=False) |
        df_filt["numero_pm"].str.contains(busca, case=False, na=False)
    ]
if filtro_disc != "(todas)":
    df_filt = df_filt[df_filt["disciplinas"].str.contains(filtro_disc, na=False)]

# =====================================================================
# 📊 TABELA
# =====================================================================
df_view = df_filt[[
    "id", "nome", "numero_pm", "total_semanal", "total_anual",
    "num_turmas", "disciplinas"
]].rename(columns={
    "id": "ID",
    "nome": "Nome completo",
    "numero_pm": "Nº PM",
    "total_semanal": "Aulas/sem",
    "total_anual": "Aulas/ano",
    "num_turmas": "Turmas",
    "disciplinas": "Disciplinas",
})

df_view.insert(0, "🗑️", False)

editado = st.data_editor(
    df_view,
    column_config={
        "🗑️": st.column_config.CheckboxColumn("🗑️", default=False, width="small"),
        "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
        "Nome completo": st.column_config.TextColumn(
            "Nome completo", disabled=True, width="large"
        ),
        "Nº PM": st.column_config.TextColumn(
            "Nº PM", disabled=True, width="small"
        ),
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
    "nome", "numero_pm", "total_semanal", "total_anual",
    "num_turmas", "disciplinas"
]].rename(columns={
    "nome": "Nome completo",
    "numero_pm": "Nº PM",
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
# ✏️ EDITAR PROFESSOR
# =====================================================================
st.divider()
st.subheader("✏️ Editar professor")
st.caption(
    "Use esta seção quando o professor foi cadastrado sem o Nº PM, "
    "ou quando precisar corrigir o nome/Nº PM depois."
)

if df.empty:
    st.info("Nenhum professor cadastrado ainda.")
else:
    with st.expander("Clique para editar", expanded=True):
        opcoes = df["id"].tolist()
        prof_edit_sel = st.selectbox(
            "Escolha o professor",
            opcoes,
            format_func=lambda x: (
                f"{df.loc[df['id'] == x, 'nome'].iloc[0]} "
                f"({df.loc[df['id'] == x, 'numero_pm'].iloc[0]})"
            ),
            key="prof_edit_sel",
        )

        prof_atual = df.loc[df["id"] == prof_edit_sel].iloc[0]
        pm_atual = "" if prof_atual["numero_pm"] == "—" else prof_atual["numero_pm"]

        with st.form("form_editar_prof"):
            c1, c2 = st.columns([3, 1])
            novo_nome = c1.text_input(
                "Nome completo",
                value=prof_atual["nome"],
            )
            novo_pm = c2.text_input(
                "Nº PM",
                value=pm_atual,
                placeholder="000000-0",
            )

            if st.form_submit_button("💾 Salvar alterações", type="primary"):
                nome_limpo = novo_nome.strip()
                num_pm = validar_numero_pm(novo_pm.strip()) if novo_pm.strip() else None

                if not nome_limpo:
                    st.error("Informe o nome completo.")
                elif novo_pm.strip() and num_pm is None:
                    st.error(
                        "Nº PM inválido. Use o formato **000000-0** "
                        "(6 dígitos + hífen + 1 dígito)."
                    )
                else:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("""
                                UPDATE professores
                                SET nome = :n, numero_pm = :pm
                                WHERE id = :id
                            """), {
                                "n": nome_limpo,
                                "pm": num_pm,
                                "id": int(prof_edit_sel),
                            })
                        st.session_state["msg_prof"] = (
                            "success",
                            f"✅ Dados de {nome_limpo} atualizados com sucesso!"
                        )
                        st.rerun()
                    except Exception as e:
                        erro = str(e).lower()
                        if "idx_professores_numero_pm" in erro or "numero_pm" in erro:
                            st.error(
                                f"⚠️ Já existe outro professor com o Nº PM {num_pm}."
                            )
                        elif "unique" in erro:
                            st.error(
                                f"⚠️ Já existe outro professor com o nome '{nome_limpo}'."
                            )
                        else:
                            st.error(f"Erro: {e}")

# =====================================================================
# 👁️ DETALHES DO PROFESSOR
# =====================================================================
st.divider()
st.subheader("👁️ Detalhes do Professor")

if df.empty:
    st.info("Nenhum professor cadastrado ainda.")
else:
    opcoes = df["id"].tolist()
    prof_sel = st.selectbox(
        "Escolha um professor para ver os detalhes",
        opcoes,
        format_func=lambda x: (
            f"{df.loc[df['id'] == x, 'nome'].iloc[0]} "
            f"({df.loc[df['id'] == x, 'numero_pm'].iloc[0]})"
        ),
        key="detalhe_prof",
    )
    prof_dados = df.loc[df["id"] == prof_sel].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nº PM", prof_dados["numero_pm"])
    c2.metric("Aulas/semana", int(prof_dados["total_semanal"]))
    c3.metric("Aulas/ano", int(prof_dados["total_anual"]))
    c4.metric("Turmas", int(prof_dados["num_turmas"]))

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
        """), conn, params={"p": int(prof_sel), "ano": ano_id})

    if detalhes.empty:
        st.info(f"ℹ️ **{prof_dados['nome']}** ainda não tem aulas atribuídas.")
    else:
        st.markdown(f"**Aulas atribuídas a {prof_dados['nome']}:**")
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
