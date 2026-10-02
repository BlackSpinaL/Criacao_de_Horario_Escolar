import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine
from core.exportar_grade import gerar_pdf_grade, gerar_excel_grade

st.set_page_config(page_title="Exportar Grade", page_icon="📄", layout="wide")
st.title("📄 Exportar Grade Horária")
st.caption("Gere PDF ou Excel para imprimir e colocar no mural.")

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

# ---------- Verifica se há grade ----------
with engine.connect() as conn:
    n_grade = conn.execute(text(
        "SELECT COUNT(*) FROM grade_gerada WHERE ano_letivo_id = :a"
    ), {"a": ano_id}).scalar()

if n_grade == 0:
    st.warning(
        "⚠️ Nenhuma grade gerada ainda. Vá em **🎯 3.2 Gerar Grade** primeiro."
    )
    st.stop()

with engine.connect() as conn:
    turmas = pd.read_sql(text("""
        SELECT t.id, t.codigo, t.nome, t.serie, t.turno
        FROM turmas t
        WHERE t.ano_letivo_id = :a
        ORDER BY t.codigo
    """), conn, params={"a": ano_id})

st.success(f"✅ {n_grade} aulas alocadas em {len(turmas)} turmas")

st.divider()

# =====================================================================
# ESCOPO
# =====================================================================
st.subheader("🎯 Escolha o que exportar")

modo = st.radio(
    "Escopo",
    ["Todas as turmas", "Selecionar turmas específicas"],
    horizontal=True,
)

if modo == "Todas as turmas":
    turmas_sel = turmas["id"].tolist()
    st.info(f"📋 **{len(turmas_sel)} turmas** serão incluídas")
else:
    turmas_sel = st.multiselect(
        "Escolha as turmas",
        turmas["id"].tolist(),
        default=turmas["id"].tolist(),
        format_func=lambda x: (
            f"{turmas.loc[turmas['id'] == x, 'codigo'].iloc[0]} — "
            f"{turmas.loc[turmas['id'] == x, 'serie'].iloc[0]}"
        ),
    )
    st.info(f"📋 **{len(turmas_sel)} turmas** selecionadas")

if not turmas_sel:
    st.warning("Selecione pelo menos 1 turma.")
    st.stop()

st.divider()

# =====================================================================
# BOTÕES DE EXPORTAÇÃO
# =====================================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 PDF (para impressão)")
    st.caption(
        "Uma página por turma, formato paisagem (A4). "
        "Ideal para imprimir e colar no mural."
    )

    if st.button("🖨️ Gerar PDF", type="primary", use_container_width=True):
        with st.spinner("Gerando PDF..."):
            try:
                pdf = gerar_pdf_grade(engine, ano_id, turmas_sel)
                st.session_state["pdf_grade"] = pdf
                st.success("✅ PDF gerado! Clique abaixo para baixar.")
            except Exception as e:
                st.error(f"Erro: {e}")

    if "pdf_grade" in st.session_state:
        st.download_button(
            "⬇️ Baixar PDF",
            st.session_state["pdf_grade"],
            f"Grade_Horaria_CTPM_{ano_row.ano}.pdf",
            "application/pdf",
            use_container_width=True,
        )

with col2:
    st.subheader("📊 Excel (para edição)")
    st.caption(
        "Uma aba consolidada + uma aba por turma. "
        "Ideal para ajustes no Excel ou Google Sheets."
    )

    if st.button("📊 Gerar Excel", type="primary", use_container_width=True):
        with st.spinner("Gerando Excel..."):
            try:
                xlsx = gerar_excel_grade(engine, ano_id, turmas_sel)
                st.session_state["xlsx_grade"] = xlsx
                st.success("✅ Excel gerado! Clique abaixo para baixar.")
            except Exception as e:
                st.error(f"Erro: {e}")

    if "xlsx_grade" in st.session_state:
        st.download_button(
            "⬇️ Baixar Excel",
            st.session_state["xlsx_grade"],
            f"Grade_Horaria_CTPM_{ano_row.ano}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

st.divider()

# =====================================================================
# PREVIEW
# =====================================================================
st.subheader("👁️ Pré-visualização (por turma)")

turma_preview = st.selectbox(
    "Escolha uma turma para pré-visualizar",
    turmas["id"].tolist(),
    format_func=lambda x: (
        f"{turmas.loc[turmas['id'] == x, 'codigo'].iloc[0]} — "
        f"{turmas.loc[turmas['id'] == x, 'serie'].iloc[0]}"
    ),
)

with engine.connect() as conn:
    dados = pd.read_sql(text("""
        SELECT h.dia, h.ordem, h.inicio, h.fim,
               c.nome AS componente, p.nome AS professor
        FROM grade_gerada g
        JOIN atividades a ON a.id = g.atividade_id
        JOIN turmas t ON t.id = a.turma_id
        JOIN horarios h ON h.id = g.horario_id
        JOIN componentes c ON c.id = a.componente_id
        JOIN professores p ON p.id = a.professor_id
        WHERE a.turma_id = :t AND g.ano_letivo_id = :a
        ORDER BY h.ordem, h.dia
    """), conn, params={"t": int(turma_preview), "a": ano_id})

if dados.empty:
    st.info("Nenhuma aula atribuída a esta turma.")
else:
    dados["cell"] = dados["componente"] + "\n(" + dados["professor"] + ")"
    pivot = dados.pivot_table(
        index=["ordem", "inicio", "fim"],
        columns="dia",
        values="cell",
        aggfunc="first",
    ).fillna("")
    pivot.index = [f"{o}ª aula\n({i}-{f})" for o, i, f in pivot.index]

    st.dataframe(pivot, use_container_width=True)
