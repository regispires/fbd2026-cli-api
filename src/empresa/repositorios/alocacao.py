from decimal import Decimal

from psycopg import Connection
from psycopg.rows import class_row

from empresa.consultas import sql_de
from empresa.dto import AlocacaoDetalhe


class AlocacaoRepositorio:
    def __init__(self, conn: Connection):
        self.conn = conn

    def carga_semanal(self, cpf: str) -> Decimal:
        (total,) = self.conn.execute(sql_de("aloc_carga"), {"cpf": cpf}).fetchone()
        return total

    def inserir(self, cpf: str, projnumero: int, horas: Decimal) -> None:
        self.conn.execute(
            sql_de("aloc_inserir"), {"cpf": cpf, "projnumero": projnumero, "horas": horas}
        )

    def remover(self, cpf: str, projnumero: int) -> bool:
        cur = self.conn.execute(sql_de("aloc_remover"), {"cpf": cpf, "projnumero": projnumero})
        return cur.fetchone() is not None

    def por_projeto(self, projnumero: int) -> list[AlocacaoDetalhe]:
        with self.conn.cursor(row_factory=class_row(AlocacaoDetalhe)) as cur:
            return cur.execute(sql_de("aloc_por_projeto"), {"projnumero": projnumero}).fetchall()
