"""Motor de geração de grade horária usando OR-Tools CP-SAT."""
from collections import defaultdict
from ortools.sat.python import cp_model
from sqlalchemy import text
from core.db import get_engine


def _popular_horarios(conn, ano_id):
    """Cria registros na tabela 'horarios' se ainda não existirem."""
    total = conn.execute(
        text("SELECT COUNT(*) FROM horarios WHERE grade_id IN "
             "(SELECT id FROM grades_horarias WHERE ano_letivo_id = :a)"),
        {"a": ano_id},
    ).scalar()
    if total > 0:
        return

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
                ), {"g": grade_id, "d": dia, "o": ordem, "i": inicio, "f": fim})


def gerar_grade(timeout_segundos=30):
    """Roda o solver e devolve estatísticas + lista de alocações."""
    engine = get_engine()

    with engine.begin() as conn:
        ano_id = conn.execute(
            text("SELECT id FROM anos_letivos WHERE ativo = TRUE LIMIT 1")
        ).scalar()
        if ano_id is None:
            return {"erro": "Nenhum ano letivo ativo. Rode o seed 2026."}

        _popular_horarios(conn, ano_id)

        atividades = conn.execute(text("""
            SELECT a.id, a.professor_id, a.turma_id, a.aulas_semana,
                   p.nome AS prof_nome, c.nome AS comp_nome, t.nome AS turma_nome,
                   t.grade_horaria_id
            FROM atividades a
            JOIN professores p ON p.id = a.professor_id
            JOIN componentes c ON c.id = a.componente_id
            JOIN turmas t      ON t.id = a.turma_id
            WHERE a.ano_letivo_id = :a
        """), {"a": ano_id}).fetchall()

        if not atividades:
            return {"erro": "Nenhuma atribuição cadastrada. Cadastre na página Atribuições."}

        horarios = conn.execute(text("""
            SELECT h.id, h.grade_id, h.dia, h.ordem
            FROM horarios h
            JOIN grades_horarias g ON g.id = h.grade_id
            WHERE g.ano_letivo_id = :a
        """), {"a": ano_id}).fetchall()

        restricoes = conn.execute(text("""
            SELECT rp.professor_id, rp.horario_id
            FROM restricoes_professor rp
        """)).fetchall()

    horarios_por_grade = defaultdict(list)
    for h in horarios:
        horarios_por_grade[h.grade_id].append(h)

    indisponiveis = defaultdict(set)
    for r in restricoes:
        indisponiveis[r.professor_id].add(r.horario_id)

    model = cp_model.CpModel()
    aloc = {}

    for i, atv in enumerate(atividades):
        for h in horarios_por_grade[atv.grade_horaria_id]:
            aloc[(i, h.id)] = model.NewBoolVar(f"a{i}_h{h.id}")

    # R1: cada atribuição deve ter exatamente N aulas
    for i, atv in enumerate(atividades):
        vars_possiveis = [aloc[(i, h.id)]
                          for h in horarios_por_grade[atv.grade_horaria_id]]
        if len(vars_possiveis) < atv.aulas_semana:
            return {"erro": f"Turma {atv.turma_nome} tem poucos horários "
                            f"para {atv.comp_nome} ({atv.aulas_semana} aulas)."}
        model.Add(sum(vars_possiveis) == atv.aulas_semana)

    # R2: professor não pode estar em 2 lugares no mesmo horário
    for h_id in {h.id for h in horarios}:
        for prof_id in {a.professor_id for a in atividades}:
            vars_prof = [aloc[(i, h_id)]
                         for i, a in enumerate(atividades)
                         if a.professor_id == prof_id and (i, h_id) in aloc]
            if len(vars_prof) > 1:
                model.AddAtMostOne(vars_prof)

    # R3: turma não pode ter 2 aulas no mesmo horário
    for h_id in {h.id for h in horarios}:
        for turma_id in {a.turma_id for a in atividades}:
            vars_turma = [aloc[(i, h_id)]
                          for i, a in enumerate(atividades)
                          if a.turma_id == turma_id and (i, h_id) in aloc]
            if len(vars_turma) > 1:
                model.AddAtMostOne(vars_turma)

    # R4: no máx 2 aulas da mesma disciplina por dia (sem consecutivas)
    for i, atv in enumerate(atividades):
        horarios_atv = horarios_por_grade[atv.grade_horaria_id]
        por_dia = defaultdict(list)
        for h in horarios_atv:
            if (i, h.id) in aloc:
                por_dia[h.dia].append(h)

        for dia, hs in por_dia.items():
            hs_ord = sorted(hs, key=lambda x: x.ordem)
            if len(hs_ord) > 2:
                model.Add(sum(aloc[(i, h.id)] for h in hs_ord) <= 2)
            for j in range(len(hs_ord) - 1):
                h1, h2 = hs_ord[j], hs_ord[j + 1]
                if h2.ordem == h1.ordem + 1:
                    model.AddAtMostOne([aloc[(i, h1.id)], aloc[(i, h2.id)]])

    # R5: indisponibilidade dos professores
    for i, atv in enumerate(atividades):
        for h_id in indisponiveis.get(atv.professor_id, set()):
            if (i, h_id) in aloc:
                model.Add(aloc[(i, h_id)] == 0)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout_segundos
    solver.parameters.num_search_workers = 4

    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"erro": "Não foi possível encontrar solução. Verifique conflitos."}

    alocacoes = []
    for i, atv in enumerate(atividades):
        for h in horarios_por_grade[atv.grade_horaria_id]:
            if (i, h.id) in aloc and solver.Value(aloc[(i, h.id)]) == 1:
                alocacoes.append({
                    "atividade_id": atv.id,
                    "horario_id": h.id,
                    "professor": atv.prof_nome,
                    "componente": atv.comp_nome,
                    "turma": atv.turma_nome,
                    "dia": h.dia,
                    "ordem": h.ordem,
                })

    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM grade_gerada WHERE ano_letivo_id = :a"),
            {"a": ano_id},
        )
        for al in alocacoes:
            conn.execute(text(
                "INSERT INTO grade_gerada (ano_letivo_id, atividade_id, horario_id) "
                "VALUES (:a, :at, :h)"
            ), {"a": ano_id, "at": al["atividade_id"], "h": al["horario_id"]})

    return {
        "sucesso": True,
        "total_alocacoes": len(alocacoes),
        "total_aulas_esperadas": sum(a.aulas_semana for a in atividades),
        "tempo": round(solver.WallTime(), 2),
        "status": solver.StatusName(status),
        "alocacoes": alocacoes,
    }
