from psycopg import Connection, sql
from psycopg.rows import class_row

from empresa.consultas import sql_de
from empresa.dto import Projeto, ProjetoAlteracao, ProjetoNovo
from empresa.erros import DadosInvalidos

EDITAVEIS = frozenset(ProjetoAlteracao.model_fields)


class ProjetoRepositorio:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.rf = class_row(Projeto)

    def inserir(self, p: ProjetoNovo) -> Projeto:
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(sql_de("proj_inserir"), p.model_dump()).fetchone()

    def obter(self, projnumero: int) -> Projeto | None:
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(sql_de("proj_por_numero"), {"projnumero": projnumero}).fetchone()

    def listar(self, dnum: int | None = None) -> list[Projeto]:
        with self.conn.cursor(row_factory=self.rf) as cur:
            if dnum is None:
                return cur.execute(sql_de("proj_listar")).fetchall()
            return cur.execute(sql_de("proj_listar_por_dep"), {"dnum": dnum}).fetchall()

    def atualizar(self, projnumero: int, mudancas: dict) -> Projeto | None:
        if not mudancas or mudancas.keys() - EDITAVEIS:
            raise DadosInvalidos("Campos inválidos para atualização")
        sets = sql.SQL(", ").join(
            sql.SQL("{} = {}").format(sql.Identifier(c), sql.Placeholder(c)) for c in mudancas
        )
        q = sql.SQL(
            "UPDATE projeto SET {} WHERE projnumero = %(projnumero)s"
            " RETURNING projnumero, projnome, projlocal, dnum"
        ).format(sets)
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(q, {**mudancas, "projnumero": projnumero}).fetchone()

    def remover(self, projnumero: int) -> bool:
        cur = self.conn.execute(sql_de("proj_remover"), {"projnumero": projnumero})
        return cur.fetchone() is not None
