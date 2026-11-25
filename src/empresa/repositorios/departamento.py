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

    def obter(self, id: int) -> Departamento | None:
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(sql_de("dep_por_id"), {"id": id}).fetchone()

    def listar(self) -> list[Departamento]:
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(sql_de("dep_listar")).fetchall()

    def renomear(self, id: int, dnome: str) -> Departamento | None:
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(sql_de("dep_renomear"), {"id": id, "dnome": dnome}).fetchone()

    def definir_gerente(self, id: int, gerente_id: int) -> bool:
        cur = self.conn.execute(sql_de("dep_definir_gerente"), {"id": id, "gerente_id": gerente_id})
        return cur.rowcount == 1

    def remover(self, id: int) -> bool:
        cur = self.conn.execute(sql_de("dep_remover"), {"id": id})
        return cur.fetchone() is not None
