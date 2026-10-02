import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine
from core.duplicar_ano import duplicar_ano, ativar_ano, deletar_ano

st.set_page_config(page_title="Gerenciar Anos", page_icon="🗓️", layout="wide")
st.title("🗓️ Gerenciar Anos Letivos")
st.caption("Duplique a estrutura de um ano para o outro, ative ou remova anos.")

engine = get_engine()

# ---------- Mensagens ----------
if "msg_ano" in st.session_state:
    tipo, texto = st.session_state.pop("msg_ano")
    getattr(st, tipo)(texto)

# =====================================================================
# LISTA DE ANOS
# =====================================================================
with engine.connect() as conn:
    anos = pd.read_sql(text("""
        SELECT id, ano, dias_letivos, ativo, criado_em
        FROM anos_letivos
        ORDER BY ano DESC
    """), conn)

st.subheader(f"Anos cadastrados ({len(anos)})")

if anos.empty:
    st.warning("Nenhum ano cadastrado ainda. Vá para a página inicial e carregue os dados de 2026.")
    st.stop()

# ---------- Enriquece com contadores ----------
with engine.connect() as conn:
    for idx, row in anos.iterrows():
        ano_id = row["id"]
        anos.loc[idx, "n_turmas"] = conn.execute(text(
            "SELECT COUNT(*) FROM turmas WHERE ano_letivo_id = :a"
        ), {"a": ano_id}).scalar()
        anos.loc[idx, "n_matrizes"] = conn.execute(text(
            "SELECT COUNT(*) FROM matrizes WHERE ano_letivo_id = :a"
        ), {"a": ano_id}).scalar()
        anos.loc[idx, "n_grades"] = conn.execute(text(
            "SELECT COUNT(*) FROM grades_horarias WHERE ano_letivo_id = :a"
        ), {"a": ano_id}).scalar()
        anos.loc[idx, "n_atividades"] = conn.execute(text(
            "SELECT COUNT(*) FROM atividades WHERE ano_letivo_id = :a"
        ), {"a": ano_id}).scalar()
        anos.loc[idx, "n_versoes"] = conn.execute(text(
            "SELECT COUNT(*) FROM grade_versoes WHERE ano_letivo_id = :a"
        ), {"a": ano_id}).scalar()

anos["ativo_str"] = anos["ativo"].apply(lambda x: "✅ Ativo" if x else "—")

st.dataframe(
    anos[[
        "ano", "ativo_str", "n_turmas", "n_matrizes",
        "n_grades", "n_atividades", "n_versoes", "criado_em"
    ]].rename(columns={
        "ano": "Ano",
        "ativo_str": "Status",
        "n_turmas": "Turmas",
        "n_matrizes": "Matrizes",
        "n_grades": "Grades",
        "n_atividades": "Atividades",
        "n_versoes": "Versões",
        "criado_em": "Criado em",
    }),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# =====================================================================
# ATIVAR ANO
# =====================================================================
st.subheader("🎯 Trocar ano ativo")
st.caption("O ano ativo é o que aparece nas outras páginas do sistema.")

ativo_atual = anos.loc[anos["ativo"] == True, "ano"].tolist()

if ativo_atual:
    st.info(f"📅 Ano ativo atual: **{ativo_atual[0]}**")

opcoes_ano = anos["ano"].tolist()
ano_ativar = st.selectbox(
    "Escolher ano para ativar",
    opcoes_ano,
    index=0 if not ativo_atual else opcoes_ano.index(ativo_atual[0]),
    key="ano_ativar",
)

if st.button("🔄 Ativar este ano", type="primary"):
    try:
        ativar_ano(engine, int(ano_ativar))
        st.session_state["msg_ano"] = (
            "success", f"✅ Ano {ano_ativar} ativado! "
            "Recarregue as outras páginas para ver os dados dele."
        )
        st.rerun()
    except Exception as e:
        st.session_state["msg_ano"] = ("error", f"Erro: {e}")
        st.rerun()

st.divider()

# =====================================================================
# DUPLICAR ANO
# =====================================================================
st.subheader("📋 Duplicar ano letivo")
st.caption(
    "Cria um novo ano copiando toda a estrutura do ano de origem. "
    "Útil para virar o ano (ex: 2026 → 2027)."
)

with st.form("form_duplicar"):
    c1, c2, c3 = st.columns([1, 1, 2])

    origem = c1.selectbox(
        "Ano de origem",
        anos["ano"].tolist(),
        index=0,
    )
    destino = c2.number_input(
        "Novo ano",
        min_value=2026,
        max_value=2100,
        value=int(origem) + 1,
        step=1,
    )

    st.markdown("**O que copiar:**")
    cc1, cc2, cc3 = st.columns(3)
    copiar_grades = cc1.checkbox("Grades horárias", value=True,
        help="Estrutura de aulas por turno (Fund I tarde, EM manhã, etc.)")
    copiar_matrizes = cc2.checkbox("Matrizes curriculares", value=True,
        help="Aulas por componente em cada série")
    copiar_turmas = cc3.checkbox("Turmas", value=True,
        help="As turmas do ano (códigos, séries)")

    st.caption(
        "ℹ️ **Componentes e professores** são compartilhados entre os anos — "
        "não precisam ser duplicados."
    )

    if st.form_submit_button("📋 Duplicar agora", type="primary"):
        try:
            resumo = duplicar_ano(
                engine,
                ano_origem=int(origem),
                ano_destino=int(destino),
                copiar_professores=True,
                copiar_turmas=copiar_turmas,
                copiar_matrizes=copiar_matrizes,
                copiar_grades=copiar_grades,
            )

            if resumo["erro"]:
                st.session_state["msg_ano"] = ("error", f"❌ {resumo['erro']}")
            else:
                msg = (
                    f"✅ Ano **{destino}** criado!\n\n"
                    f"- {resumo['grades_ok']} grades horárias\n"
                    f"- {resumo['slots_ok']} slots\n"
                    f"- {resumo['matrizes_ok']} matrizes\n"
                    f"- {resumo['itens_ok']} itens de matriz\n"
                    f"- {resumo['turmas_ok']} turmas\n\n"
                    f"💡 Vá em **🎯 Trocar ano ativo** para ativar o {destino}."
                )
                st.session_state["msg_ano"] = ("success", msg)
            st.rerun()
        except Exception as e:
            st.session_state["msg_ano"] = ("error", f"Erro: {e}")
            st.rerun()

st.divider()

# =====================================================================
# DELETAR ANO
# =====================================================================
st.subheader("🗑️ Deletar ano letivo")
st.error(
    "⚠️ **Cuidado:** deletar um ano apaga **permanentemente** todos os dados "
    "vinculados (turmas, matrizes, grades, atividades, versões de grade). "
    "Esta ação **NÃO PODE SER DESFEITA**."
)

with st.expander("🗑️ Deletar ano (clique para expandir)"):
    if len(anos) <= 1:
        st.info("Você só tem 1 ano cadastrado. Não é possível deletar o único ano.")
    else:
        ano_del = st.selectbox(
            "Escolha o ano a deletar",
            anos["ano"].tolist(),
            key="ano_del",
        )
        ano_del_id = int(anos.loc[anos["ano"] == ano_del, "id"].iloc[0])

        # Verifica se é o ativo
        eh_ativo = bool(anos.loc[anos["ano"] == ano_del, "ativo"].iloc[0])
        if eh_ativo:
            st.warning(
                f"⚠️ **{ano_del} é o ano ativo.** Ative outro ano primeiro "
                "antes de deletar este."
            )

        confirma_check = st.checkbox(
            f"☑️ Confirmo deletar o ano **{ano_del}** e todos os dados vinculados"
        )
        confirma_texto = st.text_input(
            f"Digite o número **{ano_del}** para confirmar:",
            key="confirma_del_ano",
        )

        pode_deletar = (
            confirma_check
            and confirma_texto.strip() == str(ano_del)
            and not eh_ativo
        )

        if st.button(
            f"🗑️ Deletar {ano_del}",
            type="primary",
            disabled=not pode_deletar,
        ):
            try:
                deletar_ano(engine, int(ano_del))
                st.session_state["msg_ano"] = (
                    "success", f"🗑️ Ano {ano_del} deletado permanentemente."
                )
                st.rerun()
            except Exception as e:
                st.session_state["msg_ano"] = ("error", f"Erro: {e}")
                st.rerun()

        if not pode_deletar:
            st.caption(
                "☝️ Marque o checkbox e digite o número do ano para liberar "
                "o botão."
            )

st.divider()

# =====================================================================
# INFORMAÇÕES
# =====================================================================
with st.expander("ℹ️ Como funciona a duplicação"):
    st.markdown("""
    ### O que é copiado

    | Item | Comportamento |
    |---|---|
    | **Ano letivo** | Novo registro criado |
    | **Grades horárias** | Cópia completa (slots por turno) |
    | **Matrizes curriculares** | Cópia completa (aulas por componente) |
    | **Turmas** | Cópia completa (códigos, séries) |
    | **Componentes** | **Compartilhados** entre os anos |
    | **Professores** | **Compartilhados** entre os anos |

    ### O que **não** é copiado

    - **Atribuições** (professor × turma × disciplina) — você recadastra no novo ano
    - **Disponibilidade dos professores** — reenvia o link para cada um
    - **Versões de grade** — cada ano começa do zero

    ### Fluxo típico

    1. Duplicar 2026 → 2027
    2. Ativar 2027
    3. Ajustar turmas (cadastrar as novas)
    4. Ajustar matrizes (se mudou algo)
    5. Cadastrar atribuições
    6. Enviar link de disponibilidade
    7. Gerar grade
    """)
