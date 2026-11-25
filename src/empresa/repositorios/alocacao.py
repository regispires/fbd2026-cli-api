from decimal import Decimal

from psycopg import Connection
from psycopg.rows import class_row

from empresa.consultas import sql_de
from empresa.dto import AlocacaoDetalhe


class AlocacaoRepositorio:
    def __init__(self, conn: Connection):
        self.conn = conn

    def carga_semanal(self, funcionario_id: int) -> Decimal:
        (total,) = self.conn.execute(
            sql_de("aloc_carga"), {"funcionario_id": funcionario_id}
        ).fetchone()
        return total

    def inserir(self, funcionario_id: int, projeto_id: int, horas: Decimal) -> None:
        self.conn.execute(
            sql_de("aloc_inserir"),
            {"funcionario_id": funcionario_id, "projeto_id": projeto_id, "horas": horas},
        )

    def remover(self, funcionario_id: int, projeto_id: int) -> bool:
        cur = self.conn.execute(
            sql_de("aloc_remover"), {"funcionario_id": funcionario_id, "projeto_id": projeto_id}
        )
        return cur.fetchone() is not None

    def por_projeto(self, projeto_id: int) -> list[AlocacaoDetalhe]:
        with self.conn.cursor(row_factory=class_row(AlocacaoDetalhe)) as cur:
            return cur.execute(sql_de("aloc_por_projeto"), {"projeto_id": projeto_id}).fetchall()
