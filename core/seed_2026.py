"""Seed 2026 - Popula o banco com dados oficiais do CTPM/Lavras."""
from sqlalchemy import text
from core.db import get_engine


# =====================================================================
# COMPONENTES CURRICULARES
# (nome, area, pratica_lab, agrupa_com)
# =====================================================================
COMPONENTES = [
    ("Língua Portuguesa", "Linguagens", False, None),
    ("Produção Textual", "Linguagens", False, "Língua Portuguesa"),
    ("Língua Inglesa", "Linguagens", False, None),
    ("Arte", "Linguagens", False, None),
    ("Educação Física", "Linguagens", False, None),
    ("Matemática", "Matemática", False, None),
    ("Ciências", "Ciências", False, None),
    ("Geografia", "Humanas", False, None),
    ("História", "Humanas", False, None),
    ("Ed. Socioemocional e Ensino Religioso", "Ensino Religioso", False, None),
    ("Língua Portuguesa 1", "Linguagens", False, None),
    ("Língua Portuguesa 2", "Linguagens", False, "Língua Portuguesa 1"),
    ("Ciências/Lab", "Ciências", True, "Ciências"),
    ("Literatura", "Linguagens", False, "Língua Portuguesa"),
    ("Oficina de Textos", "Linguagens", False, None),
    ("Língua Inglesa na Prática", "Linguagens", False, None),
    ("Educação Física na Prática", "Linguagens", False, None),
    ("Física", "Ciências", False, None),
    ("Física/Lab", "Ciências", True, "Física"),
    ("Química", "Ciências", False, None),
    ("Química na Prática", "Ciências", True, "Química"),
    ("Biologia", "Ciências", False, None),
    ("Biologia na Prática", "Ciências", True, "Biologia"),
    ("Ciências da Natureza para o ENEM", "Ciências", False, None),
    ("Sociologia", "Humanas", False, None),
    ("Filosofia", "Humanas", False, None),
    ("Projeto de Vida", "Humanas", False, None),
    ("Desenvolvimento Sustentável", "Humanas", False, None),
    ("Educação para Profissões", "Humanas", False, None),
    ("Educação Financeira", "Matemática", False, None),
    ("Matemática e Estatística", "Matemática", False, None),
]


# =====================================================================
# GRADES DE HORÁRIO
# (chave, titulo, turno, dias, [(ordem, nome, inicio, fim, tipo), ...])
# =====================================================================
GRADES = [
    ("fund1_tarde", "1º ao 5º ano - Tarde", "Tarde",
     "Segunda,Terça,Quarta,Quinta,Sexta", [
        (1, "1ª aula", "13:00", "13:50", "aula"),
        (2, "2ª aula", "13:50", "14:40", "aula"),
        (3, "3ª aula", "14:40", "15:30", "aula"),
        (4, "Recreio", "15:30", "15:50", "intervalo"),
        (5, "4ª aula", "15:50", "16:40", "aula"),
        (6, "5ª aula", "16:40", "17:30", "aula"),
    ]),
    ("fund2_tarde", "6º e 7º ano - Tarde", "Tarde",
     "Segunda,Terça,Quarta,Quinta,Sexta", [
        (1, "1ª aula", "13:00", "13:45", "aula"),
        (2, "2ª aula", "13:45", "14:30", "aula"),
        (3, "3ª aula", "14:30", "15:15", "aula"),
        (4, "Recreio", "15:15", "15:30", "intervalo"),
        (5, "4ª aula", "15:30", "16:15", "aula"),
        (6, "5ª aula", "16:15", "17:00", "aula"),
        (7, "Intervalo", "17:00", "17:05", "intervalo"),
        (8, "6ª aula", "17:05", "17:50", "aula"),
    ]),
    ("fund2_manha", "8º e 9º ano - Manhã", "Manhã",
     "Segunda,Terça,Quarta,Quinta,Sexta", [
        (1, "1ª aula", "07:00", "07:45", "aula"),
        (2, "2ª aula", "07:45", "08:30", "aula"),
        (3, "3ª aula", "08:30", "09:15", "aula"),
        (4, "Recreio", "09:15", "09:30", "intervalo"),
        (5, "4ª aula", "09:30", "10:15", "aula"),
        (6, "5ª aula", "10:15", "11:00", "aula"),
        (7, "6ª aula", "11:05", "11:50", "aula"),
    ]),
    ("medio_manha", "1º, 2º e 3º EM - Manhã", "Manhã",
     "Segunda,Terça,Quarta,Quinta,Sexta", [
        (1, "1ª aula", "07:00", "07:45", "aula"),
        (2, "2ª aula", "07:45", "08:30", "aula"),
        (3, "3ª aula", "08:30", "09:15", "aula"),
        (4, "Recreio", "09:15", "09:30", "intervalo"),
        (5, "4ª aula", "09:30", "10:15", "aula"),
        (6, "5ª aula", "10:15", "11:00", "aula"),
        (7, "6ª aula", "11:05", "11:50", "aula"),
        (8, "7ª aula", "11:50", "12:35", "aula"),
    ]),
    ("medio3_tarde", "3º EM - Tarde (Ter/Qui)", "Tarde",
     "Terça,Quinta", [
        (1, "1ª aula", "13:00", "13:45", "aula"),
        (2, "2ª aula", "13:45", "14:30", "aula"),
        (3, "3ª aula", "14:30", "15:15", "aula"),
        (4, "Recreio", "15:15", "15:30", "intervalo"),
        (5, "4ª aula", "15:30", "16:15", "aula"),
        (6, "5ª aula", "16:15", "17:00", "aula"),
        (7, "6ª aula", "17:05", "17:50", "aula"),
    ]),
]


# =====================================================================
# MATRIZES CURRICULARES
# {serie: [(componente, aulas, grupo_opcao, turno_extra), ...]}
# =====================================================================
MATRIZES = {
    "1º ano": [
        ("Língua Portuguesa", 4, None, None),
        ("Produção Textual", 2, None, None),
        ("Língua Inglesa", 2, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 2, None, None),
        ("Matemática", 6, None, None),
        ("Ciências", 3, None, None),
        ("Geografia", 3, None, None),
        ("História", 2, None, None),
        ("Ed. Socioemocional e Ensino Religioso", 1, None, None),
    ],
    "2º ano": [
        ("Língua Portuguesa", 4, None, None),
        ("Produção Textual", 2, None, None),
        ("Língua Inglesa", 2, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 2, None, None),
        ("Matemática", 6, None, None),
        ("Ciências", 3, None, None),
        ("Geografia", 3, None, None),
        ("História", 2, None, None),
        ("Ed. Socioemocional e Ensino Religioso", 1, None, None),
    ],
    "3º ano": [
        ("Língua Portuguesa", 4, None, None),
        ("Produção Textual", 2, None, None),
        ("Língua Inglesa", 2, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 2, None, None),
        ("Matemática", 5, None, None),
        ("Ciências", 3, None, None),
        ("Geografia", 3, None, None),
        ("História", 3, None, None),
        ("Ed. Socioemocional e Ensino Religioso", 1, None, None),
    ],
    "4º ano": [
        ("Língua Portuguesa", 4, None, None),
        ("Produção Textual", 2, None, None),
        ("Língua Inglesa", 2, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 2, None, None),
        ("Matemática", 5, None, None),
        ("Ciências", 3, None, None),
        ("Geografia", 3, None, None),
        ("História", 3, None, None),
        ("Ed. Socioemocional e Ensino Religioso", 1, None, None),
    ],
    "5º ano": [
        ("Língua Portuguesa", 4, None, None),
        ("Produção Textual", 2, None, None),
        ("Língua Inglesa", 2, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 2, None, None),
        ("Matemática", 5, None, None),
        ("Ciências", 3, None, None),
        ("Geografia", 3, None, None),
        ("História", 3, None, None),
        ("Ed. Socioemocional e Ensino Religioso", 1, None, None),
    ],
    "6º ano": [
        ("Língua Portuguesa 1", 4, None, None),
        ("Língua Portuguesa 2", 2, None, None),
        ("Língua Inglesa", 4, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 2, None, None),
        ("Matemática", 6, None, None),
        ("Ciências", 3, None, None),
        ("Geografia", 3, None, None),
        ("História", 4, None, None),
        ("Ed. Socioemocional e Ensino Religioso", 1, None, None),
    ],
    "7º ano": [
        ("Língua Portuguesa 1", 4, None, None),
        ("Língua Portuguesa 2", 2, None, None),
        ("Língua Inglesa", 4, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 2, None, None),
        ("Matemática", 6, None, None),
        ("Ciências", 4, None, None),
        ("Geografia", 3, None, None),
        ("História", 3, None, None),
        ("Ed. Socioemocional e Ensino Religioso", 1, None, None),
    ],
    "8º ano": [
        ("Língua Portuguesa 1", 4, None, None),
        ("Língua Portuguesa 2", 2, None, None),
        ("Língua Inglesa", 3, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 2, None, None),
        ("Matemática", 6, None, None),
        ("Ciências", 3, None, None),
        ("Geografia", 4, None, None),
        ("História", 4, None, None),
        ("Ed. Socioemocional e Ensino Religioso", 1, None, None),
    ],
    "9º ano": [
        ("Língua Portuguesa 1", 4, None, None),
        ("Língua Portuguesa 2", 2, None, None),
        ("Língua Inglesa", 3, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 2, None, None),
        ("Matemática", 6, None, None),
        ("Ciências", 4, None, None),
        ("Geografia", 4, None, None),
        ("História", 3, None, None),
        ("Ed. Socioemocional e Ensino Religioso", 1, None, None),
    ],
    "1º EM": [
        ("Língua Portuguesa", 2, None, None),
        ("Literatura", 2, None, None),
        ("Língua Inglesa", 1, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 1, None, None),
        ("Matemática", 4, None, None),
        ("Física", 3, None, None),
        ("Química", 3, None, None),
        ("Biologia", 3, None, None),
        ("Geografia", 2, None, None),
        ("História", 3, None, None),
        ("Sociologia", 1, None, None),
        ("Filosofia", 1, None, None),
        ("Projeto de Vida", 1, None, None),
        ("Oficina de Textos", 2, None, None),
        ("Língua Inglesa na Prática", 2, None, None),
        ("Biologia na Prática", 1, None, None),
        ("Química na Prática", 1, None, None),
    ],
    "2º EM": [
        ("Língua Portuguesa", 2, None, None),
        ("Literatura", 2, None, None),
        ("Língua Inglesa", 1, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 1, None, None),
        ("Matemática", 4, None, None),
        ("Física", 3, None, None),
        ("Química", 3, None, None),
        ("Biologia", 3, None, None),
        ("Geografia", 2, None, None),
        ("História", 3, None, None),
        ("Sociologia", 1, None, None),
        ("Filosofia", 1, None, None),
        ("Projeto de Vida", 1, None, None),
        ("Oficina de Textos", 2, None, None),
        ("Língua Inglesa na Prática", 2, None, None),
        ("Biologia na Prática", 1, None, None),
        ("Química na Prática", 1, None, None),
    ],
    "3º EM": [
        ("Língua Portuguesa", 3, None, None),
        ("Literatura", 2, None, None),
        ("Língua Inglesa", 1, None, None),
        ("Arte", 1, None, None),
        ("Educação Física", 1, None, None),
        ("Matemática", 5, None, None),
        ("Física", 4, None, None),
        ("Química", 3, None, None),
        ("Biologia", 3, None, None),
        ("Geografia", 3, None, None),
        ("História", 3, None, None),
        ("Sociologia", 1, None, None),
        ("Filosofia", 1, None, None),
        ("Projeto de Vida", 1, None, None),
        ("Oficina de Textos", 2, None, "Tarde"),
        ("Língua Inglesa na Prática", 2, None, "Tarde"),
        ("Biologia na Prática", 1, None, None),
        ("Química na Prática", 1, None, None),
        ("Ciências da Natureza para o ENEM", 1, None, "Tarde"),
        ("Educação Física na Prática", 1, None, "Tarde"),
        ("Matemática e Estatística", 1, "IF_ELETIVA", "Tarde"),
        ("Educação para Profissões", 1, "IF_ELETIVA", "Tarde"),
    ],
}


# =====================================================================
# TURMAS 2026 (códigos reais da planilha)
# =====================================================================
TURMAS = [
    ("12101", "1º ano", "EFAI", "Tarde", "fund1_tarde"),
    ("12102", "1º ano", "EFAI", "Tarde", "fund1_tarde"),
    ("12201", "2º ano", "EFAI", "Tarde", "fund1_tarde"),
    ("12202", "2º ano", "EFAI", "Tarde", "fund1_tarde"),
    ("12203", "2º ano", "EFAI", "Tarde", "fund1_tarde"),
    ("12301", "3º ano", "EFAI", "Tarde", "fund1_tarde"),
    ("12302", "3º ano", "EFAI", "Tarde", "fund1_tarde"),
    ("12401", "4º ano", "EFAI", "Tarde", "fund1_tarde"),
    ("12402", "4º ano", "EFAI", "Tarde", "fund1_tarde"),
    ("12501", "5º ano", "EFAI", "Tarde", "fund1_tarde"),
    ("12502", "5º ano", "EFAI", "Tarde", "fund1_tarde"),
    ("12601", "6º ano", "EFAF", "Tarde", "fund2_tarde"),
    ("12602", "6º ano", "EFAF", "Tarde", "fund2_tarde"),
    ("12701", "7º ano", "EFAF", "Tarde", "fund2_tarde"),
    ("12702", "7º ano", "EFAF", "Tarde", "fund2_tarde"),
    ("12703", "7º ano", "EFAF", "Tarde", "fund2_tarde"),
    ("11801", "8º ano", "EFAF", "Manhã", "fund2_manha"),
    ("11802", "8º ano", "EFAF", "Manhã", "fund2_manha"),
    ("11803", "8º ano", "EFAF", "Manhã", "fund2_manha"),
    ("11901", "9º ano", "EFAF", "Manhã", "fund2_manha"),
    ("11902", "9º ano", "EFAF", "Manhã", "fund2_manha"),
    ("11903", "9º ano", "EFAF", "Manhã", "fund2_manha"),
    ("21101", "1º EM", "EM", "Manhã", "medio_manha"),
    ("21102", "1º EM", "EM", "Manhã", "medio_manha"),
    ("21103", "1º EM", "EM", "Manhã", "medio_manha"),
    ("21201", "2º EM", "EM", "Manhã", "medio_manha"),
    ("21202", "2º EM", "EM", "Manhã", "medio_manha"),
    ("21301", "3º EM", "EM", "Manhã", "medio_manha"),
    ("21302", "3º EM", "EM", "Manhã", "medio_manha"),
]


def _descobrir_segmento(serie):
    """Descobre se é EFAI, EFAF ou EM a partir da série."""
    if "EM" in serie:
        return "EM"
    if serie.endswith("ano"):
        try:
            num = int(serie.split("º")[0])
            return "EFAI" if num <= 5 else "EFAF"
        except (ValueError, IndexError):
            return "EFAF"
    return "EFAF"


def rodar_seed():
    """Insere todos os dados iniciais. Retorna mensagem."""
    engine = get_engine()
    with engine.begin() as conn:
        existe = conn.execute(
            text("SELECT id FROM anos_letivos WHERE ano = 2026")
        ).first()
        if existe:
            return "⚠️ O seed 2026 já foi rodado antes. Nada foi alterado."

        # 1. Ano letivo
        conn.execute(text(
            "INSERT INTO anos_letivos (ano, dias_letivos, ativo) "
            "VALUES (2026, 200, TRUE)"
        ))
        ano_id = conn.execute(
            text("SELECT id FROM anos_letivos WHERE ano = 2026")
        ).scalar()

        # 2. Componentes
        for nome, area, prac, agr in COMPONENTES:
            conn.execute(text(
                "INSERT INTO componentes (nome, area, pratica_lab, agrupa_com) "
                "VALUES (:n, :a, :p, :g)"
            ), {"n": nome, "a": area, "p": prac, "g": agr})

        # 3. Grades horárias + slots
        for chave, titulo, turno, dias, slots in GRADES:
            conn.execute(text(
                "INSERT INTO grades_horarias "
                "(ano_letivo_id, chave, titulo, turno, dias_semana) "
                "VALUES (:a, :c, :t, :tn, :d)"
            ), {"a": ano_id, "c": chave, "t": titulo, "tn": turno, "d": dias})
            grade_id = conn.execute(text(
                "SELECT id FROM grades_horarias WHERE chave = :c"
            ), {"c": chave}).scalar()

            for ordem, nome_slot, inicio, fim, tipo in slots:
                conn.execute(text(
                    "INSERT INTO slots_horario "
                    "(grade_id, ordem, nome, inicio, fim, tipo) "
                    "VALUES (:g, :o, :n, :i, :f, :t)"
                ), {"g": grade_id, "o": ordem, "n": nome_slot,
                    "i": inicio, "f": fim, "t": tipo})

        # 4. Matrizes + itens
        for serie, itens in MATRIZES.items():
            segmento = _descobrir_segmento(serie)
            conn.execute(text(
                "INSERT INTO matrizes (ano_letivo_id, segmento, serie) "
                "VALUES (:a, :s, :sr)"
            ), {"a": ano_id, "s": segmento, "sr": serie})
            matriz_id = conn.execute(text(
                "SELECT id FROM matrizes "
                "WHERE ano_letivo_id = :a AND serie = :s"
            ), {"a": ano_id, "s": serie}).scalar()

            for comp_nome, aulas, grupo, turno_extra in itens:
                comp_id = conn.execute(text(
                    "SELECT id FROM componentes WHERE nome = :n"
                ), {"n": comp_nome}).scalar()
                if comp_id is None:
                    conn.execute(text(
                        "INSERT INTO componentes (nome) VALUES (:n)"
                    ), {"n": comp_nome})
                    comp_id = conn.execute(text(
                        "SELECT id FROM componentes WHERE nome = :n"
                    ), {"n": comp_nome}).scalar()

                conn.execute(text(
                    "INSERT INTO itens_matriz "
                    "(matriz_id, componente_id, aulas_semana, "
                    " grupo_opcao, turno_extra) "
                    "VALUES (:m, :c, :a, :g, :t)"
                ), {"m": matriz_id, "c": comp_id, "a": aulas,
                    "g": grupo, "t": turno_extra})

        # 5. Turmas
        for codigo, serie, segmento, turno, grade_chave in TURMAS:
            grade_id = conn.execute(text(
                "SELECT id FROM grades_horarias WHERE chave = :c"
            ), {"c": grade_chave}).scalar()
            conn.execute(text(
                "INSERT INTO turmas "
                "(ano_letivo_id, codigo, nome, serie, turno, "
                " segmento, grade_horaria_id) "
                "VALUES (:a, :c, :n, :s, :t, :sg, :g)"
            ), {"a": ano_id, "c": codigo, "n": f"{serie} ({codigo})",
                "s": serie, "t": turno, "sg": segmento, "g": grade_id})

    return "✅ Seed 2026 concluído com sucesso!"


def status_banco():
    """Retorna contagens para exibir no app."""
    engine = get_engine()
    with engine.connect() as conn:
        return {
            "anos": conn.execute(text("SELECT COUNT(*) FROM anos_letivos")).scalar(),
            "componentes": conn.execute(text("SELECT COUNT(*) FROM componentes")).scalar(),
            "grades": conn.execute(text("SELECT COUNT(*) FROM grades_horarias")).scalar(),
            "slots": conn.execute(text("SELECT COUNT(*) FROM slots_horario")).scalar(),
            "matrizes": conn.execute(text("SELECT COUNT(*) FROM matrizes")).scalar(),
            "itens": conn.execute(text("SELECT COUNT(*) FROM itens_matriz")).scalar(),
            "turmas": conn.execute(text("SELECT COUNT(*) FROM turmas")).scalar(),
        }
