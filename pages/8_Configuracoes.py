import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Configurações", page_icon="⚙️", layout="wide")
st.title("⚙️ Configurações do Sistema")
st.caption("Ferramentas administrativas — use com cuidado.")

engine = get_engine()

# =====================================================================
# 📊 STATUS ATUAL DO BANCO
# =====================================================================
st.subheader("📊 Status atual do banco")

with engine.connect() as conn:
    status = {
        "Anos letivos": conn.execute(text("SELECT COUNT(*) FROM anos_letivos")).scalar(),
        "Componentes": conn.execute(text("SELECT COUNT(*) FROM componentes")).scalar(),
        "Grades horárias": conn.execute(text("SELECT COUNT(*) FROM grades_horarias")).scalar(),
        "Slots de horário": conn.execute(text("SELECT COUNT(*) FROM slots_horario")).scalar(),
        "Matrizes": conn.execute(text("SELECT COUNT(*) FROM matrizes")).scalar(),
        "Itens de matriz": conn.execute(text("SELECT COUNT(*) FROM itens_matriz")).scalar(),
        "Turmas": conn.execute(text("SELECT COUNT(*) FROM turmas")).scalar(),
        "Professores": conn.execute(text("SELECT COUNT(*) FROM professores")).scalar(),
        "Atividades (atribuições)": conn.execute(text("SELECT COUNT(*) FROM atividades")).scalar(),
        "Horários gerados": conn.execute(text("SELECT COUNT(*) FROM horarios")).scalar(),
        "Restrições de professor": conn.execute(text("SELECT COUNT(*) FROM restricoes_professor")).scalar(),
        "Grade gerada": conn.execute(text("SELECT COUNT(*) FROM grade_gerada")).scalar(),
    }

cols = st.columns(4)
for i, (nome, qtd) in enumerate(status.items()):
    cols[i % 4].metric(nome, qtd)

st.divider()

# =====================================================================
# 📥 BACKUP ANTES DE ZERAR
# =====================================================================
st.subheader("📥 Backup dos dados")

with st.expander("Baixar backup em CSV (recomendado antes de zerar)"):
    st.caption(
        "Baixe um arquivo com todos os dados antes de zerar. "
        "Se algo der errado, você pode restaurar manualmente."
    )
    try:
        with engine.connect() as conn:
            partes = []
            for tabela in [
                "anos_letivos", "componentes", "grades_horarias",
                "slots_horario", "matrizes", "itens_matriz", "turmas",
                "professores", "atividades", "horarios",
                "restricoes_professor", "grade_gerada",
            ]:
                df = pd.read_sql(text(f"SELECT * FROM {tabela}"), conn)
                partes.append(f"\n\n===== TABELA: {tabela} =====\n")
                partes.append(df.to_csv(index=False))

        conteudo = "".join(partes).encode("utf-8")
        st.download_button(
            "⬇️ Baixar backup completo (CSV)",
            conteudo,
            "backup_grade_escolar.csv",
            "text/csv",
        )
    except Exception as e:
        st.error(f"Erro ao gerar backup: {e}")

st.divider()

# =====================================================================
# 🗑️ ZERAR SISTEMA
# =====================================================================
st.subheader("🗑️ Zerar sistema")
st.error(
    "**Atenção:** Esta ação apaga **TODOS** os dados do sistema "
    "(professores, turmas, componentes, matrizes, atribuições, grade gerada). "
    "A **estrutura** das tabelas é mantida, mas **os dados serão perdidos**. "
    "Esta ação **NÃO PODE SER DESFEITA**."
)

# ---------- Dupla confirmação ----------
st.markdown("**Para confirmar, faça as duas coisas abaixo:**")

c1, c2 = st.columns(2)

confirma_check = c1.checkbox(
    "☑️ Eu entendo que TODOS os dados serão apagados permanentemente"
)
confirma_texto = c2.text_input(
    "Digite a palavra ZERAR (em maiúsculas) para liberar o botão:"
)

pode_zerar = confirma_check and confirma_texto.strip() == "ZERAR"

col1, col2, col3 = st.columns([1, 1, 3])

if col1.button(
    "🗑️ ZERAR TUDO AGORA",
    type="primary",
    disabled=not pode_zerar,
):
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                TRUNCATE TABLE
                    grade_gerada,
                    restricoes_professor,
                    atividades,
                    horarios,
                    turmas,
                    slots_horario,
                    grades_horarias,
                    itens_matriz,
                    matrizes,
                    componentes,
                    professores,
                    anos_letivos
                RESTART IDENTITY CASCADE
            """))
        st.session_state["msg_config"] = (
            "success",
            "🗑️ Sistema zerado com sucesso! Todos os dados foram apagados. "
            "Vá para a página inicial para rodar o seed novamente."
        )
        st.rerun()
    except Exception as e:
        st.session_state["msg_config"] = ("error", f"Erro ao zerar: {e}")
        st.rerun()

if not pode_zerar:
    col2.caption("☝️ Marque o checkbox e digite ZERAR")

# ---------- Feedback ----------
if "msg_config" in st.session_state:
    tipo, texto = st.session_state.pop("msg_config")
    getattr(st, tipo)(texto)

st.divider()

# =====================================================================
# 🌱 RODAR SEED NOVAMENTE
# =====================================================================
st.subheader("🌱 Recarregar dados oficiais 2026")
st.caption(
    "Se o sistema estiver vazio (após zerar), este botão recarrega os dados "
    "oficiais do CTPM/Lavras 2026: ano letivo, componentes, matrizes, "
    "grades de horário e turmas."
)

with engine.connect() as conn:
    n_anos = conn.execute(text("SELECT COUNT(*) FROM anos_letivos")).scalar()

if n_anos > 0:
    st.info(
        f"ℹ️ Já existe {n_anos} ano letivo cadastrado. "
        "O seed só funciona em banco vazio. Zere primeiro."
    )
else:
    if st.button("🚀 Rodar seed 2026", type="primary"):
        try:
            from core.seed_2026 import rodar_seed
            msg = rodar_seed()
            st.session_state["msg_config"] = ("success", msg)
            st.rerun()
        except Exception as e:
            st.session_state["msg_config"] = ("error", f"Erro: {e}")
            st.rerun()

st.divider()

# =====================================================================
# ℹ️ INFORMAÇÕES DO SISTEMA
# =====================================================================
with st.expander("ℹ️ Informações do sistema"):
    st.markdown("""
    **Sistema de Grade Horária — CTPM/Lavras**

    - **Versão:** 1.0 (2026)
    - **Banco de dados:** PostgreSQL (Supabase)
    - **Hospedagem:** Streamlit Community Cloud
    - **Repositório:** [GitHub](https://github.com/BlackSpinal/Criacao_de_Horario_Escolar)

    **Stack técnico:**
    - Python 3.11
    - Streamlit (interface)
    - SQLAlchemy (banco)
    - OR-Tools CP-SAT (solver de grade)
    - PostgreSQL (Supabase)

    **Contato do desenvolvedor:** (a preencher)
    """)
