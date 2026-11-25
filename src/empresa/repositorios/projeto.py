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

    def obter(self, id: int) -> Projeto | None:
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(sql_de("proj_por_id"), {"id": id}).fetchone()

    def listar(self, departamento_id: int | None = None) -> list[Projeto]:
        with self.conn.cursor(row_factory=self.rf) as cur:
            if departamento_id is None:
                return cur.execute(sql_de("proj_listar")).fetchall()
            return cur.execute(
                sql_de("proj_listar_por_dep"), {"departamento_id": departamento_id}
            ).fetchall()

    def atualizar(self, id: int, mudancas: dict) -> Projeto | None:
        if not mudancas or mudancas.keys() - EDITAVEIS:
            raise DadosInvalidos("Campos inválidos para atualização")
        sets = sql.SQL(", ").join(
            sql.SQL("{} = {}").format(sql.Identifier(c), sql.Placeholder(c)) for c in mudancas
        )
        q = sql.SQL(
            "UPDATE projeto SET {} WHERE id = %(id)s"
            " RETURNING id, projnome, projlocal, departamento_id"
        ).format(sets)
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(q, {**mudancas, "id": id}).fetchone()

    def remover(self, id: int) -> bool:
        cur = self.conn.execute(sql_de("proj_remover"), {"id": id})
        return cur.fetchone() is not None
