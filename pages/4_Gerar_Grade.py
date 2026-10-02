import json
from datetime import datetime
import streamlit as st
import pandas as pd
from sqlalchemy import text
from core.db import get_engine
from core.solver import gerar_grade

st.set_page_config(page_title="Gerar Grade", page_icon="🎯", layout="wide")
st.title("🎯 Gerar Grade Horária")

engine = get_engine()

with engine.connect() as conn:
    ano_id = conn.execute(
        text("SELECT id FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
    ).scalar()

if ano_id is None:
    st.warning("Rode o seed 2026 primeiro.")
    st.stop()

# ---------- Métricas ----------
with engine.connect() as conn:
    n_atv = conn.execute(text("SELECT COUNT(*) FROM atividades")).scalar()
    n_grade = conn.execute(
        text("SELECT COUNT(*) FROM grade_gerada WHERE ano_letivo_id = :a"),
        {"a": ano_id},
    ).scalar()
    n_rest = conn.execute(
        text("SELECT COUNT(*) FROM restricoes_professor")
    ).scalar()
    n_versoes = conn.execute(
        text("SELECT COUNT(*) FROM grade_versoes WHERE ano_letivo_id = :a"),
        {"a": ano_id},
    ).scalar()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Atribuições", n_atv)
c2.metric("Alocações na grade atual", n_grade)
c3.metric("Restrições de professor", n_rest)
c4.metric("Versões salvas", n_versoes)

st.divider()

if n_atv == 0:
    st.warning("⚠️ Cadastre atribuições primeiro (página Atribuições).")
    st.stop()

# ---------- Gerar ----------
if st.button("🚀 Gerar nova grade", type="primary"):
    with st.spinner("Rodando o solver..."):
        resultado = gerar_grade(timeout_segundos=60)

    if "erro" in resultado:
        st.error(f"❌ {resultado['erro']}")
    else:
        # Salva versão
        nome_versao = (
            f"v{n_versoes + 1} — "
            f"{datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        )
        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO grade_versoes
                    (ano_letivo_id, nome, status, alocacoes, total_alocacoes)
                    VALUES (:a, :n, :s, :al, :tot)
                """), {
                    "a": ano_id,
                    "n": nome_versao,
                    "s": "rascunho",
                    "al": json.dumps(resultado["alocacoes"]),
                    "tot": resultado["total_alocacoes"],
                })

            st.success(
                f"✅ **{nome_versao}** gerada! "
                f"{resultado['total_alocacoes']} alocações em "
                f"{resultado['tempo']}s ({resultado['status']})."
            )
            st.balloons()
            st.rerun()

        except Exception as e:
            st.error(f"Erro ao salvar versão: {e}")

# ---------- Grade atual ----------
if n_grade > 0:
    st.subheader(f"📋 Grade atual ({n_grade} alocações)")

    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT p.nome AS professor, c.nome AS componente,
                   t.nome AS turma, h.dia, h.ordem, h.inicio, h.fim
            FROM grade_gerada g
            JOIN atividades a ON a.id = g.atividade_id
            JOIN professores p ON p.id = a.professor_id
            JOIN componentes c ON c.id = a.componente_id
            JOIN turmas t     ON t.id = a.turma_id
            JOIN horarios h   ON h.id = g.horario_id
            WHERE g.ano_letivo_id = :ano
            ORDER BY t.nome, h.dia, h.ordem
        """), conn, params={"ano": ano_id})

    filtro = st.selectbox(
        "Filtrar por turma",
        ["Todas"] + sorted(df["turma"].unique()),
    )
    if filtro != "Todas":
        df = df[df["turma"] == filtro]

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️ Baixar CSV",
        df.to_csv(index=False).encode("utf-8"),
        "grade_gerada.csv",
        "text/csv",
    )

st.divider()

# ---------- Histórico de versões ----------
st.subheader("📚 Histórico de versões")

with engine.connect() as conn:
    versoes = pd.read_sql(text("""
        SELECT id, nome, status, total_alocacoes, criado_em
        FROM grade_versoes
        WHERE ano_letivo_id = :a
        ORDER BY id DESC
    """), conn, params={"a": ano_id})

if versoes.empty:
    st.info("Nenhuma versão salva ainda. Clique em **🚀 Gerar nova grade**.")
else:
    st.dataframe(
        versoes.rename(columns={
            "id": "ID",
            "nome": "Versão",
            "status": "Status",
            "total_alocacoes": "Alocações",
            "criado_em": "Criada em",
        }),
        use_container_width=True,
        hide_index=True,
    )

    c_acao1, c_acao2, c_acao3 = st.columns([2, 2, 3])

    ver_id = c_acao1.selectbox(
        "Escolher versão",
        versoes["id"].tolist(),
        format_func=lambda x: versoes.loc[versoes["id"] == x, "nome"].iloc[0],
    )

    ver_status = versoes.loc[versoes["id"] == ver_id, "status"].iloc[0]

    if c_acao2.button("♻️ Restaurar esta versão"):
        try:
            with engine.connect() as conn:
                aloc_json = conn.execute(text(
                    "SELECT alocacoes FROM grade_versoes WHERE id = :id"
                ), {"id": int(ver_id)}).scalar()

            alocacoes = json.loads(aloc_json) if isinstance(aloc_json, str) else aloc_json

            with engine.begin() as conn:
                conn.execute(text(
                    "DELETE FROM grade_gerada WHERE ano_letivo_id = :a"
                ), {"a": ano_id})

                for al in alocacoes:
                    conn.execute(text(
                        "INSERT INTO grade_gerada "
                        "(ano_letivo_id, atividade_id, horario_id) "
                        "VALUES (:a, :at, :h)"
                    ), {"a": ano_id, "at": al["atividade_id"],
                        "h": al["horario_id"]})

                # Marcar como a versão atual aprovada
                conn.execute(text(
                    "UPDATE grade_versoes SET status = 'aprovada' WHERE id = :id"
                ), {"id": int(ver_id)})
                conn.execute(text(
                    "UPDATE grade_versoes SET status = 'rascunho' "
                    "WHERE id != :id AND ano_letivo_id = :a"
                ), {"id": int(ver_id), "a": ano_id})

            st.success(f"✅ Versão restaurada e marcada como aprovada!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao restaurar: {e}")

    if c_acao3.button("🗑️ Deletar versão selecionada"):
        try:
            with engine.begin() as conn:
                conn.execute(text(
                    "DELETE FROM grade_versoes WHERE id = :id"
                ), {"id": int(ver_id)})
            st.success("Versão deletada!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")
