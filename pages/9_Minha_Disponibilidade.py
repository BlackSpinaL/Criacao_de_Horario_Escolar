import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine
from core.gerar_planilha_disponibilidade import gerar_planilha_bytes

st.set_page_config(page_title="Disponibilidade", page_icon="🚫", layout="wide")
st.title("🚫 Minha Disponibilidade")
st.caption(
    "**Marque com ✓ os horários em que você PODE dar aula.** "
    "Deixe em branco os horários em que **NÃO PODE**. "
    "Se você não marcar nada em um turno, entenderemos que você "
    "**não está disponível** naquele turno."
)

engine = get_engine()

# =====================================================================
# ANO LETIVO
# =====================================================================
with engine.connect() as conn:
    ano_id = conn.execute(
        text("SELECT id FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
    ).scalar()

if ano_id is None:
    st.warning("Sistema ainda não foi inicializado. Avise a coordenação.")
    st.stop()

# =====================================================================
# GARANTE QUE HORÁRIOS EXISTEM
# =====================================================================
with engine.begin() as conn:
    total = conn.execute(
        text("SELECT COUNT(*) FROM horarios h "
             "JOIN grades_horarias g ON g.id = h.grade_id "
             "WHERE g.ano_letivo_id = :a"),
        {"a": ano_id},
    ).scalar()

    if total == 0:
        grades = conn.execute(text(
            "SELECT id, dias_semana FROM grades_horarias WHERE ano_letivo_id = :a"
        ), {"a": ano_id}).fetchall()

        for grade_id, dias_str in grades:
            dias = [d.strip() for d in dias_str.split(",")]
            slots = conn.execute(text(
                "SELECT ordem, inicio, fim FROM slots_horario "
                "WHERE grade_id = :g AND tipo = 'aula' ORDER BY ordem"
            ), {"g": grade_id}).fetchall()

            for dia in dias:
                for ordem, inicio, fim in slots:
                    conn.execute(text(
                        "INSERT INTO horarios (grade_id, dia, ordem, inicio, fim) "
                        "VALUES (:g, :d, :o, :i, :f)"
                    ), {"g": grade_id, "d": dia, "o": ordem,
                        "i": inicio, "f": fim})

# =====================================================================
# CARREGA PROFESSORES (com numero_pm)
# =====================================================================
with engine.connect() as conn:
    profs = pd.read_sql(
        text("SELECT id, nome, numero_pm FROM professores ORDER BY nome"), conn
    )

if profs.empty:
    st.warning("Nenhum professor cadastrado ainda. Avise a coordenação.")
    st.stop()

# =====================================================================
# LINK COMPARTILHÁVEL (query param)
# Aceita ?prof=Nome+Completo OU ?pm=123456-7 (prioridade: pm)
# =====================================================================
param_prof = st.query_params.get("prof", None)
param_pm = st.query_params.get("pm", None)

if param_prof:
    param_prof = param_prof.replace("+", " ")

idx_default = 0

# Tenta primeiro por Nº PM
if param_pm:
    matches = profs[profs["numero_pm"] == param_pm]
    if not matches.empty:
        idx_default = profs.index.get_loc(matches.index[0])

# Depois por nome
elif param_prof and param_prof in profs["nome"].values:
    idx_default = profs["nome"].tolist().index(param_prof)

# =====================================================================
# CONFIGURAÇÃO DOS TURNOS
# =====================================================================
DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]

TURNOS = {
    "Vespertino": {
        "grades": ["fund1_tarde", "fund2_tarde", "medio3_tarde"],
        "num_aulas": 6,
        "icone": "🌇",
    },
    "Matutino": {
        "grades": ["fund2_manha", "medio_manha"],
        "num_aulas": 7,
        "icone": "🌅",
    },
}

# =====================================================================
# SELEÇÃO DO PROFESSOR
# =====================================================================
c1, c2 = st.columns([2, 3])
prof_nome = c1.selectbox(
    "👤 Selecione seu nome",
    profs["nome"].tolist(),
    index=idx_default,
)
prof_id = int(profs.loc[profs["nome"] == prof_nome, "id"].iloc[0])

with engine.connect() as conn:
    disc_prof = conn.execute(text("""
        SELECT DISTINCT c.nome
        FROM atividades a
        JOIN componentes c ON c.id = a.componente_id
        WHERE a.professor_id = :p AND a.ano_letivo_id = :a
        ORDER BY c.nome
    """), {"p": prof_id, "a": ano_id}).fetchall()

lista_disc_prof = [d.nome for d in disc_prof]

if lista_disc_prof:
    c2.markdown(
        f"**📚 Disciplinas atribuídas:** {', '.join(lista_disc_prof)}"
    )
else:
    c2.markdown("**📚 Disciplinas atribuídas:** _(nenhuma ainda)_")

# =====================================================================
# LINK COMPARTILHÁVEL
# =====================================================================
with st.expander("🔗 Link compartilhável deste professor"):
    base_url = (
        "https://sistemadecriacaodehorarioescolar.streamlit.app/"
        "Minha_Disponibilidade"
    )

    prof_row = profs.loc[profs["id"] == prof_id].iloc[0]
    num_pm = prof_row["numero_pm"]

    col_l1, col_l2 = st.columns(2)

    with col_l1:
        st.markdown("**🔗 Por Nº PM** (recomendado)")
        if num_pm:
            link_pm = f"{base_url}?pm={num_pm}"
            st.code(link_pm, language=None)
        else:
            st.caption("_Professor sem Nº PM cadastrado_")

    with col_l2:
        st.markdown("**🔗 Por nome** (alternativa)")
        link_nome = f"{base_url}?prof={prof_nome.replace(' ', '+')}"
        st.code(link_nome, language=None)

    st.caption(
        "📋 Copie o link **por Nº PM** (mais seguro — ninguém confunde com "
        "outro professor). O professor abrirá a página já com o nome dele "
        "selecionado."
    )

st.divider()

# =====================================================================
# CARREGA HORÁRIOS
# =====================================================================
with engine.connect() as conn:
    horarios_df = pd.read_sql(text("""
        SELECT h.id, h.grade_id, h.dia, h.ordem,
               g.chave AS grade_chave,
               ROW_NUMBER() OVER (
                   PARTITION BY h.grade_id, h.dia ORDER BY h.ordem
               ) AS pos
        FROM horarios h
        JOIN grades_horarias g ON g.id = h.grade_id
        WHERE g.ano_letivo_id = :a
    """), conn, params={"a": ano_id})

with engine.connect() as conn:
    res = conn.execute(text(
        "SELECT horario_id FROM restricoes_professor WHERE professor_id = :p"
    ), {"p": prof_id}).fetchall()
restricoes_existentes = {r.horario_id for r in res}

ja_salvou = len(restricoes_existentes) > 0

# =====================================================================
# MONTA GRIDS
# =====================================================================
grids = {}
for turno, cfg in TURNOS.items():
    horarios_turno = horarios_df[horarios_df["grade_chave"].isin(cfg["grades"])]
    if horarios_turno.empty:
        continue

    dias_turno = [d for d in DIAS if d in horarios_turno["dia"].unique()]

    df = pd.DataFrame(
        False,
        index=range(1, cfg["num_aulas"] + 1),
        columns=dias_turno,
    )
    df.index = [f"{i}º horário" for i in df.index]

    if ja_salvou:
        for _, h in horarios_turno.iterrows():
            pos = int(h["pos"])
            dia = h["dia"]
            if pos > cfg["num_aulas"]:
                continue
            if dia not in df.columns:
                continue
            if h["id"] not in restricoes_existentes:
                df.loc[f"{pos}º horário", dia] = True

    grids[turno] = df

# =====================================================================
# RENDERIZA GRIDS
# =====================================================================
resultados = {}

for turno, cfg in TURNOS.items():
    if turno not in grids:
        continue

    st.subheader(
        f"{cfg['icone']} {turno.upper()} — {cfg['num_aulas']} aulas de 45 min"
    )
    st.caption(
        f"Marque os horários em que você **pode** dar aula no turno da "
        f"{turno.lower()}. Se você não dá aula nesse turno, "
        f"**deixe tudo desmarcado**."
    )

    editado = st.data_editor(
        grids[turno],
        column_config={
            dia: st.column_config.CheckboxColumn(
                dia, default=False, width="small"
            )
            for dia in grids[turno].columns
        },
        hide_index=False,
        use_container_width=True,
        key=f"grid_{turno}",
    )
    resultados[turno] = editado

    st.write("")

# =====================================================================
# AÇÕES
# =====================================================================
st.divider()

col_salvar, col_export, col_export_preenchido = st.columns(3)

if col_salvar.button("💾 Salvar minha disponibilidade", type="primary"):
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "DELETE FROM restricoes_professor WHERE professor_id = :p"
            ), {"p": prof_id})

            total_restricoes = 0
            total_disponiveis = 0

            for turno, cfg in TURNOS.items():
                if turno not in resultados:
                    continue
                grid = resultados[turno]

                horarios_turno = horarios_df[
                    horarios_df["grade_chave"].isin(cfg["grades"])
                ]

                for _, h in horarios_turno.iterrows():
                    pos = int(h["pos"])
                    dia = h["dia"]
                    if pos > cfg["num_aulas"]:
                        continue
                    if dia not in grid.columns:
                        continue

                    linha = f"{pos}º horário"
                    if linha not in grid.index:
                        continue

                    disponivel = bool(grid.loc[linha, dia])

                    if disponivel:
                        total_disponiveis += 1
                    else:
                        conn.execute(text(
                            "INSERT INTO restricoes_professor "
                            "(professor_id, horario_id) VALUES (:p, :h)"
                        ), {"p": prof_id, "h": int(h["id"])})
                        total_restricoes += 1

        st.success(
            f"✅ Disponibilidade de **{prof_nome}** salva! "
            f"({total_disponiveis} horários disponíveis · "
            f"{total_restricoes} bloqueados)"
        )
        st.balloons()
        st.rerun()

    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# ---------- Exportar em branco ----------
planilha_branco = gerar_planilha_bytes(prof_nome, lista_disc_prof)
col_export.download_button(
    "📥 Exportar planilha em branco",
    planilha_branco,
    f"Disponibilidade_{prof_nome.replace(' ', '_')}.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

if ja_salvou:
    col_export_preenchido.download_button(
        "📥 Baixar com marcações",
        planilha_branco,
        f"Disponibilidade_{prof_nome.replace(' ', '_')}_preenchida.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

# =====================================================================
# RODAPÉ
# =====================================================================
with engine.connect() as conn:
    n_rest = conn.execute(text(
        "SELECT COUNT(*) FROM restricoes_professor WHERE professor_id = :p"
    ), {"p": prof_id}).scalar()

st.caption(
    f"ℹ️ Atualmente **{prof_nome}** tem **{n_rest} horários bloqueados**. "
    f"Marque os disponíveis e clique em Salvar para atualizar."
)
