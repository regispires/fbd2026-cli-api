from psycopg import Connection
from psycopg.rows import class_row

from empresa.consultas import sql_de
from empresa.dto import Departamento, DepartamentoNovo


class DepartamentoRepositorio:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.rf = class_row(Departamento)

    def inserir(self, d: DepartamentoNovo) -> Departamento:
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(sql_de("dep_inserir"), d.model_dump()).fetchone()

    def obter(self, dnumero: int) -> Departamento | None:
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(sql_de("dep_por_numero"), {"dnumero": dnumero}).fetchone()

    def listar(self) -> list[Departamento]:
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(sql_de("dep_listar")).fetchall()

    def renomear(self, dnumero: int, dnome: str) -> Departamento | None:
        with self.conn.cursor(row_factory=self.rf) as cur:
            cur.execute(sql_de("dep_renomear"), {"dnumero": dnumero, "dnome": dnome})
            return cur.fetchone()

    def definir_gerente(self, dnumero: int, cpf: str) -> bool:
        cur = self.conn.execute(sql_de("dep_definir_gerente"), {"dnumero": dnumero, "cpf": cpf})
        return cur.rowcount == 1

    def remover(self, dnumero: int) -> bool:
        cur = self.conn.execute(sql_de("dep_remover"), {"dnumero": dnumero})
        return cur.fetchone() is not None
