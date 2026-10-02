import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine

st.set_page_config(page_title="Turmas", page_icon="🏫", layout="wide")
st.title("🏫 Turmas")

engine = get_engine()

with engine.connect() as conn:
    ano_row = conn.execute(
        text("SELECT id, ano FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
    ).first()

if ano_row is None:
    st.warning("Rode o seed 2026 primeiro.")
    st.stop()

ano_id = ano_row.id
st.caption(f"📅 Ano letivo: **{ano_row.ano}**")

with engine.connect() as conn:
    grades = pd.read_sql(text(
        "SELECT id, chave, titulo, turno FROM grades_horarias "
        "WHERE ano_letivo_id = :a ORDER BY titulo"
    ), conn, params={"a": ano_id})

if "msg_turma" in st.session_state:
    tipo, texto = st.session_state.pop("msg_turma")
    getattr(st, tipo)(texto)

# =====================================================================
# ➕ CADASTRO
# =====================================================================
with st.form("nova_turma", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
    codigo = c1.text_input("Código", placeholder="11801")
    serie = c2.text_input("Série", placeholder="8º ano")
    grade_id = c3.selectbox(
        "Turno/Segmento",
        grades["id"].tolist(),
        format_func=lambda x: grades.loc[grades["id"] == x, "titulo"].iloc[0],
    )
    alunos = c4.number_input("Alunos", 0, 100, 0, step=1)

    if st.form_submit_button("➕ Adicionar", type="primary"):
        if not codigo.strip() or not serie.strip():
            st.session_state["msg_turma"] = ("error", "Preencha código e série.")
        else:
            grade_row = grades.loc[grades["id"] == grade_id].iloc[0]
            try:
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO turmas
                        (ano_letivo_id, codigo, nome, serie, turno,
                         segmento, grade_horaria_id, alunos)
                        VALUES (:a, :c, :n, :s, :t, :sg, :g, :al)
                    """), {
                        "a": ano_id, "c": codigo.strip(),
                        "n": f"{serie.strip()} ({codigo.strip()})",
                        "s": serie.strip(), "t": grade_row["turno"],
                        "sg": grade_row["chave"], "g": int(grade_id),
                        "al": alunos,
                    })
                st.session_state["msg_turma"] = (
                    "success", f"✅ Turma {codigo.strip()} cadastrada!"
                )
            except Exception as e:
                if "unique" in str(e).lower():
                    st.session_state["msg_turma"] = (
                        "warning", f"⚠️ Código '{codigo}' já existe."
                    )
                else:
                    st.session_state["msg_turma"] = ("error", f"Erro: {e}")
            st.rerun()

# =====================================================================
# 📋 LISTA
# =====================================================================
with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT t.id, t.codigo, t.serie, t.turno, t.segmento,
               t.alunos, t.grade_horaria_id,
               g.titulo AS grade,
               COALESCE(
                   (SELECT SUM(a.aulas_semana) FROM atividades a
                    WHERE a.turma_id = t.id AND a.ano_letivo_id = :ano),
                   0
               ) AS aulas_sem
        FROM turmas t
        LEFT JOIN grades_horarias g ON g.id = t.grade_horaria_id
        WHERE t.ano_letivo_id = :ano
        ORDER BY t.codigo
    """), conn, params={"ano": ano_id})

df["aulas_ano"] = df["aulas_sem"] * 40

st.subheader(f"Cadastradas ({len(df)})")

if df.empty:
    st.info("Nenhuma turma cadastrada ainda.")
    st.stop()

# =====================================================================
# 🔎 FILTROS
# =====================================================================
col_f1, col_f2 = st.columns([2, 2])
with col_f1:
    busca = st.text_input("🔍 Buscar por código ou série",
                          placeholder="Ex: 11801 ou 8º")
with col_f2:
    segmentos_disp = ["(todos)"] + sorted(df["segmento"].dropna().unique().tolist())
    filtro_seg = st.selectbox("Filtrar por segmento", segmentos_disp)

df_filt = df.copy()
if busca:
    df_filt = df_filt[
        df_filt["codigo"].str.contains(busca, case=False, na=False) |
        df_filt["serie"].str.contains(busca, case=False, na=False)
    ]
if filtro_seg != "(todos)":
    df_filt = df_filt[df_filt["segmento"] == filtro_seg]

# =====================================================================
# 📊 TABELA
# =====================================================================
df_view = df_filt[[
    "id", "codigo", "serie", "turno", "alunos",
    "aulas_sem", "aulas_ano"
]].rename(columns={
    "id": "ID", "codigo": "Código", "serie": "Série",
    "turno": "Turno", "alunos": "Alunos",
    "aulas_sem": "Aulas/sem", "aulas_ano": "Aulas/ano",
})
df_view.insert(0, "🗑️", False)

editado = st.data_editor(
    df_view,
    column_config={
        "🗑️": st.column_config.CheckboxColumn("🗑️", default=False, width="small"),
        "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
        "Código": st.column_config.TextColumn("Código", disabled=True, width="small"),
        "Série": st.column_config.TextColumn("Série", disabled=True, width="medium"),
        "Turno": st.column_config.TextColumn("Turno", disabled=True, width="small"),
        "Alunos": st.column_config.NumberColumn("Alunos", disabled=True, width="small"),
        "Aulas/sem": st.column_config.NumberColumn("Aulas/sem", disabled=True, width="small"),
        "Aulas/ano": st.column_config.NumberColumn("Aulas/ano", disabled=True, width="small"),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_turmas",
)

st.caption(
    f"📊 **Exibindo {len(df_filt)} de {len(df)} turmas** · "
    f"{int(df_filt['aulas_sem'].sum())} aulas/semana · "
    f"{int(df_filt['aulas_ano'].sum())} aulas/ano"
)

# =====================================================================
# 📥 EXPORTAR CSV
# =====================================================================
csv = df_filt[[
    "codigo", "serie", "turno", "alunos", "aulas_sem", "aulas_ano"
]].rename(columns={
    "codigo": "Código", "serie": "Série", "turno": "Turno",
    "alunos": "Alunos", "aulas_sem": "Aulas semanais",
    "aulas_ano": "Aulas anuais",
}).to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Exportar CSV", csv, "turmas.csv", "text/csv",
)

# =====================================================================
# ✏️ EDITAR TURMA
# =====================================================================
st.divider()
st.subheader("✏️ Editar turma")

with st.expander("Clique para editar", expanded=False):
    opcoes = df["id"].tolist()
    turma_edit_sel = st.selectbox(
        "Escolha a turma",
        opcoes,
        format_func=lambda x: (
            f"{df.loc[df['id'] == x, 'codigo'].iloc[0]} — "
            f"{df.loc[df['id'] == x, 'serie'].iloc[0]}"
        ),
        key="turma_edit_sel",
    )

    turma_atual = df.loc[df["id"] == turma_edit_sel].iloc[0]
    idx_grade_atual = grades["id"].tolist().index(int(turma_atual["grade_horaria_id"]))

    with st.form("form_editar_turma"):
        c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
        novo_codigo = c1.text_input("Código", value=turma_atual["codigo"])
        nova_serie = c2.text_input("Série", value=turma_atual["serie"])
        nova_grade_id = c3.selectbox(
            "Turno/Segmento",
            grades["id"].tolist(),
            index=idx_grade_atual,
            format_func=lambda x: grades.loc[grades["id"] == x, "titulo"].iloc[0],
        )
        novos_alunos = c4.number_input(
            "Alunos", 0, 100, int(turma_atual["alunos"]), step=1
        )

        if st.form_submit_button("💾 Salvar alterações", type="primary"):
            if not novo_codigo.strip() or not nova_serie.strip():
                st.error("Código e série são obrigatórios.")
            else:
                grade_row = grades.loc[grades["id"] == nova_grade_id].iloc[0]
                try:
                    with engine.begin() as conn:
                        conn.execute(text("""
                            UPDATE turmas
                            SET codigo = :c,
                                serie = :s,
                                nome = :n,
                                turno = :t,
                                segmento = :sg,
                                grade_horaria_id = :g,
                                alunos = :al
                            WHERE id = :id
                        """), {
                            "c": novo_codigo.strip(),
                            "s": nova_serie.strip(),
                            "n": f"{nova_serie.strip()} ({novo_codigo.strip()})",
                            "t": grade_row["turno"],
                            "sg": grade_row["chave"],
                            "g": int(nova_grade_id),
                            "al": novos_alunos,
                            "id": int(turma_edit_sel),
                        })
                    st.session_state["msg_turma"] = (
                        "success",
                        f"✅ Turma {novo_codigo.strip()} atualizada!"
                    )
                    st.rerun()
                except Exception as e:
                    if "unique" in str(e).lower():
                        st.error(f"⚠️ Já existe outra turma com o código '{novo_codigo}'.")
                    else:
                        st.error(f"Erro: {e}")

# =====================================================================
# 👁️ DETALHES DA TURMA
# =====================================================================
st.divider()
st.subheader("👁️ Detalhes da Turma")

turma_sel = st.selectbox(
    "Escolha uma turma",
    df["id"].tolist(),
    format_func=lambda x: df.loc[df["id"] == x, "codigo"].iloc[0]
    + " — " + df.loc[df["id"] == x, "serie"].iloc[0],
    key="detalhe_turma",
)

turma_dados = df.loc[df["id"] == turma_sel].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Alunos", int(turma_dados["alunos"]))
c2.metric("Turno", turma_dados["turno"])
c3.metric("Aulas/sem", int(turma_dados["aulas_sem"]))
c4.metric("Aulas/ano", int(turma_dados["aulas_ano"]))

with engine.connect() as conn:
    detalhes = pd.read_sql(text("""
        SELECT
            c.nome AS "Disciplina",
            p.nome AS "Professor",
            a.aulas_semana AS "Aulas/sem",
            a.aulas_semana * 40 AS "Aulas/ano"
        FROM atividades a
        JOIN componentes c ON c.id = a.componente_id
        JOIN professores p ON p.id = a.professor_id
        WHERE a.turma_id = :t AND a.ano_letivo_id = :ano
        ORDER BY c.nome
    """), conn, params={"t": int(turma_sel), "ano": ano_id})

if detalhes.empty:
    st.info(f"ℹ️ A turma ainda não tem aulas atribuídas.")
else:
    st.markdown(f"**Aulas atribuídas à turma:**")
    st.dataframe(detalhes, use_container_width=True, hide_index=True)

# =====================================================================
# 🗑️ BARRA DE AÇÕES
# =====================================================================
marcados = editado[editado["🗑️"]]
n_marc = len(marcados)
col1, col2, _ = st.columns([2, 1, 4])

if n_marc == 0:
    col1.caption("☝️ Marque turmas na coluna 🗑️ para deletar")
else:
    ids = marcados["ID"].astype(int).tolist()
    placeholders = ",".join(str(i) for i in ids)

    with engine.connect() as conn:
        conflitos = pd.read_sql(text(f"""
            SELECT t.nome, COUNT(a.id) AS n_atv
            FROM turmas t
            LEFT JOIN atividades a ON a.turma_id = t.id
            WHERE t.id IN ({placeholders})
            GROUP BY t.id, t.nome
            HAVING COUNT(a.id) > 0
        """), conn)

    if not conflitos.empty:
        col1.warning(f"⚠️ {n_marc} turma(s) com aulas atribuídas")
        st.warning(
            "**Atenção:** turmas com atividades:\n\n" +
            "\n".join([
                f"- **{r.nome}** — {r.n_atv} atividade(s)"
                for r in conflitos.itertuples()
            ])
        )
        confirmar = st.checkbox("☑️ Confirmo deletar **e** as atividades")
        if col2.button(
            f"🗑️ Deletar ({n_marc})", type="primary", disabled=not confirmar
        ):
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"DELETE FROM atividades WHERE turma_id IN ({placeholders})"
                    ))
                    conn.execute(text(
                        f"DELETE FROM turmas WHERE id IN ({placeholders})"
                    ))
                st.session_state["msg_turma"] = (
                    "success", f"🗑️ {n_marc} turma(s) deletada(s)!"
                )
            except Exception as e:
                st.session_state["msg_turma"] = ("error", f"Erro: {e}")
            st.rerun()
    else:
        col1.warning(f"⚠️ {n_marc} turma(s) selecionada(s)")
        if col2.button(f"🗑️ Deletar ({n_marc})", type="primary"):
            try:
                with engine.begin() as conn:
                    conn.execute(text(
                        f"DELETE FROM turmas WHERE id IN ({placeholders})"
                    ))
                st.session_state["msg_turma"] = (
                    "success", f"🗑️ {n_marc} turma(s) deletada(s)!"
                )
            except Exception as e:
                st.session_state["msg_turma"] = ("error", f"Erro: {e}")
            st.rerun()
