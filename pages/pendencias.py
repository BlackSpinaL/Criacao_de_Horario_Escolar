import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Pendências", page_icon="📋", layout="wide")
st.title("📋 Painel de Pendências")
st.caption("Acompanhe o que está pendente antes de gerar a grade horária.")

engine = get_engine()

# ---------- Ano letivo ----------
with engine.connect() as conn:
    ano_row = conn.execute(
        text("SELECT id, ano FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
    ).first()

if ano_row is None:
    st.warning("Rode o seed 2026 primeiro.")
    st.stop()

ano_id = ano_row.id
st.caption(f"📅 Ano letivo: **{ano_row.ano}**")

# =====================================================================
# 1. DISPONIBILIDADE DOS PROFESSORES
# =====================================================================
st.subheader("1️⃣ Disponibilidade dos professores")

with engine.connect() as conn:
    df_disp = pd.read_sql(text("""
        SELECT
            p.id,
            p.nome,
            p.numero_pm,
            COALESCE(
                (SELECT COUNT(*) FROM restricoes_professor r
                 WHERE r.professor_id = p.id),
                0
            ) AS n_restricoes
        FROM professores p
        ORDER BY p.nome
    """), conn)

if df_disp.empty:
    st.info("Nenhum professor cadastrado ainda.")
else:
    df_disp["status"] = df_disp["n_restricoes"].apply(
        lambda x: "✅ Preencheu" if x > 0 else "❌ Não preencheu"
    )

    total = len(df_disp)
    preencheram = (df_disp["n_restricoes"] > 0).sum()
    faltam = total - preencheram

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de professores", total)
    c2.metric("✅ Preencheram", int(preencheram))
    c3.metric(
        "❌ Faltam", int(faltam),
        delta=f"-{faltam}" if faltam > 0 else None,
        delta_color="inverse" if faltam > 0 else "off",
    )

    filtro = st.radio(
        "Mostrar",
        ["Todos", "Só quem falta", "Só quem preencheu"],
        horizontal=True,
        key="filtro_disp",
    )

    df_view = df_disp.copy()
    if filtro == "Só quem falta":
        df_view = df_view[df_view["n_restricoes"] == 0]
    elif filtro == "Só quem preencheu":
        df_view = df_view[df_view["n_restricoes"] > 0]

    df_view = df_view[["nome", "numero_pm", "n_restricoes", "status"]].rename(columns={
        "nome": "Professor",
        "numero_pm": "Nº PM",
        "n_restricoes": "Horários bloqueados",
        "status": "Status",
    })

    st.dataframe(df_view, use_container_width=True, hide_index=True)

    if faltam > 0:
        st.warning(
            f"⚠️ **{faltam} professor(es) ainda não preencheram** a disponibilidade. "
            f"Envie o link individual (página 🚫 Minha Disponibilidade)."
        )

    csv = df_view.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Exportar lista de pendências",
        csv,
        "pendencias_disponibilidade.csv",
        "text/csv",
    )

st.divider()

# =====================================================================
# 2. ATRIBUIÇÕES INCOMPLETAS
# =====================================================================
st.subheader("2️⃣ Atribuições incompletas")
st.caption(
    "Turmas em que a soma de aulas atribuídas **não bate** com a matriz "
    "curricular da série."
)

with engine.connect() as conn:
    df_turmas = pd.read_sql(text("""
        SELECT
            t.id,
            t.codigo,
            t.nome,
            t.serie,
            COALESCE(
                (SELECT SUM(im.aulas_semana)
                 FROM matrizes m
                 JOIN itens_matriz im ON im.matriz_id = m.id
                 WHERE m.ano_letivo_id = :ano AND m.serie = t.serie),
                0
            ) AS aulas_matriz,
            COALESCE(
                (SELECT SUM(a.aulas_semana) FROM atividades a
                 WHERE a.turma_id = t.id AND a.ano_letivo_id = :ano),
                0
            ) AS aulas_atribuidas
        FROM turmas t
        WHERE t.ano_letivo_id = :ano
        ORDER BY t.codigo
    """), conn, params={"ano": ano_id})

if df_turmas.empty:
    st.info("Nenhuma turma cadastrada ainda.")
else:
    df_turmas["diferenca"] = df_turmas["aulas_atribuidas"] - df_turmas["aulas_matriz"]
    df_turmas["status"] = df_turmas["diferenca"].apply(
        lambda d: "✅ OK" if d == 0
        else (f"❌ Faltam {-d}" if d < 0 else f"🟡 Excedem {d}")
    )

    total_turmas = len(df_turmas)
    completas = (df_turmas["diferenca"] == 0).sum()
    incompletas = total_turmas - completas

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de turmas", total_turmas)
    c2.metric("✅ Completas", int(completas))
    c3.metric("⚠️ Incompletas", int(incompletas))

    df_mostrar = df_turmas[[
        "codigo", "serie", "aulas_matriz", "aulas_atribuidas", "status"
    ]].rename(columns={
        "codigo": "Código",
        "serie": "Série",
        "aulas_matriz": "Aulas matriz",
        "aulas_atribuidas": "Aulas atribuídas",
        "status": "Status",
    })

    if incompletas > 0:
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Todas as turmas estão 100% atribuídas!")

st.divider()

# =====================================================================
# 3. DISCIPLINAS SEM PROFESSOR
# =====================================================================
st.subheader("3️⃣ Disciplinas sem professor")
st.caption(
    "Componentes que estão na matriz mas **não têm professor atribuído** "
    "em alguma turma."
)

with engine.connect() as conn:
    df_sem_prof = pd.read_sql(text("""
        SELECT
            t.codigo AS turma,
            t.serie,
            c.nome AS componente,
            im.aulas_semana AS aulas_necessarias
        FROM turmas t
        JOIN matrizes m ON m.ano_letivo_id = t.ano_letivo_id AND m.serie = t.serie
        JOIN itens_matriz im ON im.matriz_id = m.id
        JOIN componentes c ON c.id = im.componente_id
        WHERE t.ano_letivo_id = :ano
          AND NOT EXISTS (
              SELECT 1 FROM atividades a
              WHERE a.turma_id = t.id AND a.componente_id = c.id
          )
        ORDER BY t.codigo, c.nome
    """), conn, params={"ano": ano_id})

if df_sem_prof.empty:
    st.success("✅ Todas as disciplinas têm professor atribuído em todas as turmas!")
else:
    st.warning(
        f"⚠️ **{len(df_sem_prof)} disciplina(s) sem professor**. "
        f"Vá em 🔗 Atribuições para corrigir."
    )
    st.dataframe(
        df_sem_prof.rename(columns={
            "turma": "Turma",
            "serie": "Série",
            "componente": "Componente",
            "aulas_necessarias": "Aulas/sem",
        }),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# =====================================================================
# 4. FEEDBACK DOS PROFESSORES
# =====================================================================
st.subheader("4️⃣ Feedback dos professores")
st.caption("Problemas relatados pelos professores sobre a grade gerada.")

with engine.connect() as conn:
    df_fb = pd.read_sql(text("""
        SELECT f.id, p.nome AS professor, p.numero_pm,
               f.tipo, f.mensagem, f.status, f.criado_em
        FROM feedback_professores f
        JOIN professores p ON p.id = f.professor_id
        ORDER BY
            CASE WHEN f.status = 'aberto' THEN 0 ELSE 1 END,
            f.id DESC
    """), conn)

if df_fb.empty:
    st.success("✅ Nenhum feedback pendente no momento.")
else:
    abertos = (df_fb["status"] == "aberto").sum()
    resolvidos = (df_fb["status"] != "aberto").sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df_fb))
    c2.metric("🔴 Abertos", int(abertos))
    c3.metric("✅ Resolvidos", int(resolvidos))

    filtro_fb = st.radio(
        "Mostrar",
        ["Abertos", "Todos", "Resolvidos"],
        horizontal=True,
        key="filtro_feedback",
    )

    df_fb_view = df_fb.copy()
    if filtro_fb == "Abertos":
        df_fb_view = df_fb_view[df_fb_view["status"] == "aberto"]
    elif filtro_fb == "Resolvidos":
        df_fb_view = df_fb_view[df_fb_view["status"] != "aberto"]

    st.dataframe(
        df_fb_view[[
            "professor", "numero_pm", "tipo", "mensagem",
            "status", "criado_em"
        ]].rename(columns={
            "professor": "Professor",
            "numero_pm": "Nº PM",
            "tipo": "Tipo",
            "mensagem": "Mensagem",
            "status": "Status",
            "criado_em": "Enviado em",
        }),
        use_container_width=True,
        hide_index=True,
    )

    if not df_fb_view.empty:
        col_r1, col_r2 = st.columns([2, 2])
        fb_id = col_r1.selectbox(
            "Marcar como resolvido",
            [""] + df_fb_view["id"].tolist(),
            format_func=lambda x: (
                "—" if x == "" else
                f"#{x} — "
                f"{df_fb.loc[df_fb['id'] == x, 'professor'].iloc[0]}"
            ),
            key="fb_resolver",
        )
        if fb_id and col_r2.button("✅ Marcar como resolvido"):
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        "UPDATE feedback_professores SET status = 'resolvido' "
                        "WHERE id = :id"
                    ), {"id": int(fb_id)})
                st.success("Feedback marcado como resolvido!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
