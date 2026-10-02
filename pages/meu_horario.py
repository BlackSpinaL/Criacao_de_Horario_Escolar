import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Meu Horário", page_icon="📅", layout="wide")
st.title("📅 Meu Horário")
st.caption("Consulte sua grade horária e reporte problemas à coordenação.")

engine = get_engine()

# ---------- Ano letivo ----------
with engine.connect() as conn:
    ano_id = conn.execute(
        text("SELECT id FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
    ).scalar()

if ano_id is None:
    st.warning("Sistema ainda não inicializado. Avise a coordenação.")
    st.stop()

# ---------- Professores ----------
with engine.connect() as conn:
    profs = pd.read_sql(text(
        "SELECT id, nome, numero_pm FROM professores ORDER BY nome"
    ), conn)

if profs.empty:
    st.warning("Nenhum professor cadastrado ainda.")
    st.stop()

# ---------- Query param ----------
param_pm = st.query_params.get("pm", None)
param_prof = st.query_params.get("prof", None)
if param_prof:
    param_prof = param_prof.replace("+", " ")

idx_default = 0
if param_pm:
    matches = profs[profs["numero_pm"] == param_pm]
    if not matches.empty:
        idx_default = profs.index.get_loc(matches.index[0])
elif param_prof and param_prof in profs["nome"].values:
    idx_default = profs["nome"].tolist().index(param_prof)

# ---------- Seleção ----------
prof_nome = st.selectbox(
    "👤 Selecione seu nome",
    profs["nome"].tolist(),
    index=idx_default,
)
prof_id = int(profs.loc[profs["nome"] == prof_nome, "id"].iloc[0])

st.divider()

# ---------- Grade do professor ----------
with engine.connect() as conn:
    grade = pd.read_sql(text("""
        SELECT h.dia, h.ordem, h.inicio, h.fim,
               c.nome AS componente,
               t.codigo AS turma_codigo,
               t.nome AS turma
        FROM grade_gerada g
        JOIN atividades a ON a.id = g.atividade_id
        JOIN professores p ON p.id = a.professor_id
        JOIN componentes c ON c.id = a.componente_id
        JOIN turmas t     ON t.id = a.turma_id
        JOIN horarios h   ON h.id = g.horario_id
        WHERE g.ano_letivo_id = :ano AND p.id = :p
        ORDER BY h.dia, h.ordem
    """), conn, params={"ano": ano_id, "p": prof_id})

if grade.empty:
    st.info(
        f"ℹ️ **{prof_nome}** ainda não tem aulas atribuídas na grade. "
        "Aguarde a coordenação gerar o horário."
    )
else:
    st.subheader(f"📋 Grade semanal de {prof_nome}")

    DIAS_ORDEM = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
    grade["dia"] = pd.Categorical(grade["dia"], categories=DIAS_ORDEM, ordered=True)

    # Grade visual (tabela)
    pivot = grade.pivot_table(
        index="ordem",
        columns="dia",
        values="componente",
        aggfunc="first",
    )

    pivot_turma = grade.pivot_table(
        index="ordem",
        columns="dia",
        values="turma",
        aggfunc="first",
    )

    # Junta componente + turma
    pivot_final = pivot.copy()
    for idx in pivot_final.index:
        for col in pivot_final.columns:
            comp = pivot.loc[idx, col] if idx in pivot.index and col in pivot.columns else ""
            turma = pivot_turma.loc[idx, col] if idx in pivot_turma.index and col in pivot_turma.columns else ""
            if pd.notna(comp) and comp:
                pivot_final.loc[idx, col] = f"{comp}\n({turma})"
            else:
                pivot_final.loc[idx, col] = ""

    pivot_final = pivot_final.fillna("")
    pivot_final.index = [f"{i}ª aula" for i in pivot_final.index]

    st.dataframe(
        pivot_final,
        use_container_width=True,
        height=400,
    )

    # Lista detalhada
    with st.expander("📋 Ver lista completa de aulas"):
        st.dataframe(
            grade[["dia", "ordem", "inicio", "fim", "componente", "turma"]]
            .rename(columns={
                "dia": "Dia",
                "ordem": "Aula",
                "inicio": "Início",
                "fim": "Fim",
                "componente": "Disciplina",
                "turma": "Turma",
            }),
            use_container_width=True,
            hide_index=True,
        )

    # ---------- Reportar problema ----------
    st.divider()
    st.subheader("⚠️ Reportar um problema")

    with st.form("form_feedback", clear_on_submit=True):
        tipo = st.selectbox(
            "Tipo do problema",
            [
                "Horário em conflito com outra escola",
                "Disciplina errada para mim",
                "Turma errada",
                "Aula em dia/horário que não posso",
                "Carga horária incorreta",
                "Outro",
            ],
        )
        mensagem = st.text_area(
            "Descreva o problema",
            placeholder="Ex: Não posso dar aula na segunda à 1ª aula "
                        "porque leciono em outra escola.",
        )

        if st.form_submit_button("📨 Enviar para coordenação", type="primary"):
            if not mensagem.strip():
                st.warning("Descreva o problema antes de enviar.")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("""
                            INSERT INTO feedback_professores
                            (professor_id, tipo, mensagem, status)
                            VALUES (:p, :t, :m, 'aberto')
                        """), {
                            "p": prof_id,
                            "t": tipo,
                            "m": mensagem.strip(),
                        })
                    st.success(
                        "✅ Feedback enviado à coordenação! "
                        "Você será avisado quando for resolvido."
                    )
                except Exception as e:
                    st.error(f"Erro ao enviar: {e}")

    # Meus feedbacks
    with engine.connect() as conn:
        meus_fb = pd.read_sql(text("""
            SELECT tipo, mensagem, status, criado_em
            FROM feedback_professores
            WHERE professor_id = :p
            ORDER BY id DESC
        """), conn, params={"p": prof_id})

    if not meus_fb.empty:
        with st.expander(f"📬 Meus feedbacks enviados ({len(meus_fb)})"):
            st.dataframe(
                meus_fb.rename(columns={
                    "tipo": "Tipo",
                    "mensagem": "Mensagem",
                    "status": "Status",
                    "criado_em": "Enviado em",
                }),
                use_container_width=True,
                hide_index=True,
            )
