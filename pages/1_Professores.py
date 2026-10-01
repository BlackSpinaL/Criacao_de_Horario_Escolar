import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Professores", page_icon="👨‍🏫", layout="wide")
st.title("👨‍🏫 Professores")
st.caption("Cadastre apenas o nome. O sistema calcula automaticamente o total de aulas.")

engine = get_engine()

# =====================================================================
# Mensagens de feedback
# =====================================================================
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
                    "INSERT INTO professores (nome, carga_max) "
                    "VALUES (:n, 0)"
                ), {"n": nome.strip()})
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
# 📋 LISTA COM TOTAIS CALCULADOS
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
                (SELECT COUNT(DISTINCT a.componente_id) FROM atividades a
                 WHERE a.professor_id = p.id AND a.ano_letivo_id = :ano),
                0
            ) AS num_disc,
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

st.subheader(f"Cadastrados ({len(df)})")

if df.empty:
    st.info("Nenhum professor cadastrado ainda. Use o formulário acima.")
    st.stop()

# ---------- Calcula anuais ----------
df["total_anual"] = df["total_semanal"] * 40

# ---------- Prepara exibição ----------
df_view = df[[
    "id", "nome", "total_semanal", "total_anual",
    "num_turmas", "num_disc", "disciplinas"
]].rename(columns={
    "id": "ID",
    "nome": "Nome",
    "total_semanal": "Aulas/sem",
    "total_anual": "Aulas/ano",
    "num_turmas": "Turmas",
    "num_disc": "Disc.",
    "disciplinas": "Disciplinas",
})

df_view.insert(0, "🗑️", False)

editado = st.data_editor(
    df_view,
    column_config={
        "🗑️": st.column_config.CheckboxColumn(
            "🗑️", help="Marque para deletar", default=False, width="small"
        ),
        "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
        "Nome": st.column_config.TextColumn("Nome", disabled=True, width="large"),
        "Aulas/sem": st.column_config.NumberColumn(
            "Aulas/sem", disabled=True, width="small",
            help="Total de aulas semanais em todas as turmas"
        ),
        "Aulas/ano": st.column_config.NumberColumn(
            "Aulas/ano", disabled=True, width="small",
            help="Total de aulas anuais (40 semanas)"
        ),
        "Turmas": st.column_config.NumberColumn(
            "Turmas", disabled=True, width="small",
            help="Quantidade de turmas em que leciona"
        ),
        "Disc.": st.column_config.NumberColumn(
            "Disc.", disabled=True, width="small",
            help="Quantidade de disciplinas que leciona"
        ),
        "Disciplinas": st.column_config.TextColumn(
            "Disciplinas", disabled=True, width="large"
        ),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_profs",
)

# ---------- Rodapé com totais ----------
total_geral_sem = int(df["total_semanal"].sum())
st.caption(
    f"📊 **Total geral:** {len(df)} professores · "
    f"{total_geral_sem} aulas/semana · {total_geral_sem * 40} aulas/ano"
)

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

    # Verifica se têm atividades vinculadas
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
            "**Atenção:** os professores abaixo têm aulas atribuídas. "
            "Deletá-los removerá **também** essas atribuições:\n\n" +
            "\n".join([
                f"- **{r.nome}** — {r.n_atv} aula(s)"
                for r in conflitos.itertuples()
            ])
        )
        confirmar = st.checkbox(
            "☑️ Confirmo que quero deletar **e** suas atribuições"
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
                    "success",
                    f"🗑️ {n_marc} professor(es) deletado(s)!"
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
