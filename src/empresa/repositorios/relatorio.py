import csv
from typing import TextIO

from psycopg import Connection
from psycopg.rows import class_row

from empresa.consultas import sql_de
from empresa.dto import (
    DependentesFuncionario,
    EquipeProjeto,
    FuncionarioDepartamento,
    PosicaoSalarial,
    ResumoDepartamento,
)


class RelatorioRepositorio:
    """Relatórios devolvem estruturas próprias, sem forçar DTOs de entidade."""

    def __init__(self, conn: Connection):
        self.conn = conn

    def departamentos(self) -> list[ResumoDepartamento]:
        with self.conn.cursor(row_factory=class_row(ResumoDepartamento)) as cur:
            return cur.execute(sql_de("rel_departamentos")).fetchall()

    def ranking(self, deps: list[int]) -> list[PosicaoSalarial]:
        with self.conn.cursor(row_factory=class_row(PosicaoSalarial)) as cur:
            return cur.execute(sql_de("rel_ranking"), {"deps": deps}).fetchall()

    def todos_projetos(self) -> list[FuncionarioDepartamento]:
        with self.conn.cursor(row_factory=class_row(FuncionarioDepartamento)) as cur:
            return cur.execute(sql_de("rel_todos_projetos")).fetchall()

    def equipes(self, max_func: int) -> list[EquipeProjeto]:
        with self.conn.cursor(row_factory=class_row(EquipeProjeto)) as cur:
            return cur.execute(sql_de("rel_equipes"), {"max_func": max_func}).fetchall()

    def dependentes(self, min_dep: int) -> list[DependentesFuncionario]:
        with self.conn.cursor(row_factory=class_row(DependentesFuncionario)) as cur:
            return cur.execute(sql_de("rel_dependentes"), {"min_dep": min_dep}).fetchall()

    def supervisao(self, raiz_id: int) -> list[tuple[int, str, str, int | None]]:
        return self.conn.execute(sql_de("rel_supervisao"), {"raiz": raiz_id}).fetchall()

    def exportar_csv(self, arq: TextIO) -> int:
        """Cursor nomeado: lê em lotes, com memória constante. Exige transação."""
        with self.conn.cursor(name="exp_func") as cur:
            cur.itersize = 1000
            cur.execute(sql_de("rel_exportar"))
            w = csv.writer(arq, delimiter=";")
            w.writerow([c.name for c in cur.description])
            n = 0
            for linha in cur:
                w.writerow(linha)
                n += 1
            return n
