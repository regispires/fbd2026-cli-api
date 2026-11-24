import csv
from typing import TextIO

from psycopg import Connection
from psycopg.rows import class_row

from empresa.consultas import sql_de
from empresa.dto import FuncionarioDepartamento, PosicaoSalarial, ResumoDepartamento


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

    def supervisao(self, cpf_raiz: str) -> list[tuple[str, str, str | None]]:
        return self.conn.execute(sql_de("rel_supervisao"), {"raiz": cpf_raiz}).fetchall()

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
