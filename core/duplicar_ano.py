"""Função para duplicar um ano letivo completo (matrizes, turmas, grades)."""
from sqlalchemy import text


def duplicar_ano(engine, ano_origem, ano_destino,
                 copiar_professores=True, copiar_turmas=True,
                 copiar_matrizes=True, copiar_grades=True):
    """
    Copia a estrutura de um ano letivo para outro.

    Parâmetros:
    - ano_origem: ano de origem (ex: 2026)
    - ano_destino: ano novo (ex: 2027)
    - copiar_professores: se True, não cria professores novos (são compartilhados)
    - copiar_turmas: se True, cria as turmas do novo ano
    - copiar_matrizes: se True, cria as matrizes do novo ano
    - copiar_grades: se True, cria as grades horárias do novo ano

    Retorna um dicionário com o resumo da operação.
    """
    resumo = {
        "ano_destino_id": None,
        "componentes_ok": 0,
        "grades_ok": 0,
        "slots_ok": 0,
        "matrizes_ok": 0,
        "itens_ok": 0,
        "turmas_ok": 0,
        "erro": None,
    }

    with engine.begin() as conn:
        # ---------- Verifica se o ano origem existe ----------
        origem = conn.execute(text(
            "SELECT id, dias_letivos FROM anos_letivos WHERE ano = :a"
        ), {"a": ano_origem}).first()

        if origem is None:
            resumo["erro"] = f"Ano origem {ano_origem} não encontrado."
            return resumo

        origem_id = origem.id
        dias_letivos = origem.dias_letivos or 200

        # ---------- Verifica se o ano destino já existe ----------
        destino_existente = conn.execute(text(
            "SELECT id FROM anos_letivos WHERE ano = :a"
        ), {"a": ano_destino}).first()

        if destino_existente:
            resumo["erro"] = f"Ano {ano_destino} já existe no banco."
            return resumo

        # ---------- 1. Cria o novo ano letivo ----------
        conn.execute(text("""
            INSERT INTO anos_letivos (ano, dias_letivos, ativo)
            VALUES (:a, :d, FALSE)
        """), {"a": ano_destino, "d": dias_letivos})

        destino_id = conn.execute(text(
            "SELECT id FROM anos_letivos WHERE ano = :a"
        ), {"a": ano_destino}).scalar()

        resumo["ano_destino_id"] = destino_id

        # ---------- 2. Copia as grades horárias ----------
        if copiar_grades:
            grades = conn.execute(text("""
                SELECT id, chave, titulo, turno, dias_semana
                FROM grades_horarias
                WHERE ano_letivo_id = :a
            """), {"a": origem_id}).fetchall()

            for g in grades:
                conn.execute(text("""
                    INSERT INTO grades_horarias
                    (ano_letivo_id, chave, titulo, turno, dias_semana)
                    VALUES (:a, :c, :t, :tn, :d)
                """), {
                    "a": destino_id, "c": g.chave, "t": g.titulo,
                    "tn": g.turno, "d": g.dias_semana,
                })

                nova_grade_id = conn.execute(text("""
                    SELECT id FROM grades_horarias
                    WHERE ano_letivo_id = :a AND chave = :c
                """), {"a": destino_id, "c": g.chave}).scalar()

                # Copia os slots
                slots = conn.execute(text("""
                    SELECT ordem, nome, inicio, fim, tipo
                    FROM slots_horario
                    WHERE grade_id = :g
                    ORDER BY ordem
                """), {"g": g.id}).fetchall()

                for s in slots:
                    conn.execute(text("""
                        INSERT INTO slots_horario
                        (grade_id, ordem, nome, inicio, fim, tipo)
                        VALUES (:g, :o, :n, :i, :f, :t)
                    """), {
                        "g": nova_grade_id, "o": s.ordem, "n": s.nome,
                        "i": s.inicio, "f": s.fim, "t": s.tipo,
                    })
                    resumo["slots_ok"] += 1

                resumo["grades_ok"] += 1

        # ---------- 3. Copia as matrizes curriculares ----------
        if copiar_matrizes:
            matrizes = conn.execute(text("""
                SELECT id, segmento, serie
                FROM matrizes
                WHERE ano_letivo_id = :a
            """), {"a": origem_id}).fetchall()

            for m in matrizes:
                conn.execute(text("""
                    INSERT INTO matrizes (ano_letivo_id, segmento, serie)
                    VALUES (:a, :s, :sr)
                """), {"a": destino_id, "s": m.segmento, "sr": m.serie})

                nova_matriz_id = conn.execute(text("""
                    SELECT id FROM matrizes
                    WHERE ano_letivo_id = :a AND serie = :sr
                """), {"a": destino_id, "sr": m.serie}).scalar()

                itens = conn.execute(text("""
                    SELECT componente_id, aulas_semana, obrigatoria,
                           grupo_opcao, turno_extra
                    FROM itens_matriz
                    WHERE matriz_id = :m
                """), {"m": m.id}).fetchall()

                for i in itens:
                    conn.execute(text("""
                        INSERT INTO itens_matriz
                        (matriz_id, componente_id, aulas_semana, obrigatoria,
                         grupo_opcao, turno_extra)
                        VALUES (:m, :c, :a, :o, :g, :t)
                    """), {
                        "m": nova_matriz_id, "c": i.componente_id,
                        "a": i.aulas_semana, "o": i.obrigatoria,
                        "g": i.grupo_opcao, "t": i.turno_extra,
                    })
                    resumo["itens_ok"] += 1

                resumo["matrizes_ok"] += 1

        # ---------- 4. Copia as turmas ----------
        if copiar_turmas:
            turmas = conn.execute(text("""
                SELECT codigo, nome, serie, turno, segmento,
                       alunos, grade_horaria_id
                FROM turmas
                WHERE ano_letivo_id = :a
            """), {"a": origem_id}).fetchall()

            for t in turmas:
                # Descobre a chave da grade de origem para achar a nova
                grade_origem = conn.execute(text(
                    "SELECT chave FROM grades_horarias WHERE id = :g"
                ), {"g": t.grade_horaria_id}).first()

                nova_grade_id = None
                if grade_origem:
                    nova_grade_id = conn.execute(text("""
                        SELECT id FROM grades_horarias
                        WHERE ano_letivo_id = :a AND chave = :c
                    """), {"a": destino_id, "c": grade_origem.chave}).scalar()

                conn.execute(text("""
                    INSERT INTO turmas
                    (ano_letivo_id, codigo, nome, serie, turno, segmento,
                     grade_horaria_id, alunos)
                    VALUES (:a, :c, :n, :s, :t, :sg, :g, :al)
                """), {
                    "a": destino_id, "c": t.codigo, "n": t.nome,
                    "s": t.serie, "t": t.turno, "sg": t.segmento,
                    "g": nova_grade_id, "al": t.alunos,
                })
                resumo["turmas_ok"] += 1

        # ---------- 5. Conta componentes (compartilhados) ----------
        resumo["componentes_ok"] = conn.execute(text(
            "SELECT COUNT(*) FROM componentes"
        )).scalar()

    return resumo


def ativar_ano(engine, ano):
    """Define um ano como ativo e desativa os outros."""
    with engine.begin() as conn:
        conn.execute(text("UPDATE anos_letivos SET ativo = FALSE"))
        conn.execute(text(
            "UPDATE anos_letivos SET ativo = TRUE WHERE ano = :a"
        ), {"a": ano})
    return True


def deletar_ano(engine, ano):
    """Deleta um ano letivo (e todos os dados vinculados em cascata)."""
    with engine.begin() as conn:
        conn.execute(text(
            "DELETE FROM anos_letivos WHERE ano = :a"
        ), {"a": ano})
    return True
