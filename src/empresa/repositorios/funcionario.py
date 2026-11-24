from decimal import Decimal

from psycopg import Connection, sql
from psycopg.rows import class_row

from empresa.consultas import sql_de
from empresa.dto import (
    Funcionario,
    FuncionarioAlteracao,
    FuncionarioNovo,
    FuncionarioResumo,
)
from empresa.erros import DadosInvalidos
from empresa.validacao import escapar_like

# lista branca de colunas atualizáveis: os campos do modelo de alteração
EDITAVEIS = frozenset(FuncionarioAlteracao.model_fields)


class FuncionarioRepositorio:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.rf = class_row(Funcionario)

    def inserir(self, f: FuncionarioNovo) -> Funcionario:
        with self.conn.cursor(row_factory=self.rf) as cur:
            cur.execute(sql_de("func_inserir"), f.model_dump())
            return cur.fetchone()

    def obter(self, cpf: str) -> Funcionario | None:
        with self.conn.cursor(row_factory=self.rf) as cur:
            cur.execute(sql_de("func_por_cpf"), {"cpf": cpf})
            return cur.fetchone()

    def bloquear(self, cpf: str) -> bool:
        cur = self.conn.execute(sql_de("func_bloquear"), {"cpf": cpf})
        return cur.fetchone() is not None

    def buscar(
        self,
        *,
        dnr: int | None = None,
        nome: str | None = None,
        salario_min: Decimal | None = None,
        limite: int = 20,
        offset: int = 0,
    ) -> list[FuncionarioResumo]:
        """Filtros opcionais compostos com sql.SQL; valores sempre como parâmetros."""
        conds = []
        p = {"lim": limite, "off": offset}
        if dnr is not None:
            conds.append(sql.SQL("dnumero = %(dnr)s"))
            p["dnr"] = dnr
        if salario_min is not None:
            conds.append(sql.SQL("salario >= %(smin)s"))
            p["smin"] = salario_min
        if nome:
            conds.append(sql.SQL("nome ILIKE %(nome)s"))
            p["nome"] = "%" + escapar_like(nome) + "%"
        where = sql.SQL(" AND ").join(conds) if conds else sql.SQL("TRUE")
        q = sql.SQL(
            "SELECT cpf, nome, dnumero, dnome, salario"
            "  FROM vw_funcionario_depto WHERE {}"
            " ORDER BY nome, cpf LIMIT %(lim)s OFFSET %(off)s"
        ).format(where)
        with self.conn.cursor(row_factory=class_row(FuncionarioResumo)) as cur:
            return cur.execute(q, p).fetchall()

    def atualizar(self, cpf: str, mudancas: dict) -> Funcionario | None:
        if not mudancas or mudancas.keys() - EDITAVEIS:
            raise DadosInvalidos("Campos inválidos para atualização")
        sets = sql.SQL(", ").join(
            sql.SQL("{} = {}").format(sql.Identifier(c), sql.Placeholder(c)) for c in mudancas
        )
        q = sql.SQL(
            "UPDATE funcionario SET {} WHERE cpf = %(cpf)s"
            " RETURNING cpf, pnome, minicial, unome, datanasc, endereco,"
            " sexo, salario, cpf_supervisor, dnr"
        ).format(sets)
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(q, {**mudancas, "cpf": cpf}).fetchone()

    def mudar_departamento(self, cpf: str, dnr: int) -> bool:
        cur = self.conn.execute(sql_de("func_mudar_dep"), {"cpf": cpf, "dnr": dnr})
        return cur.rowcount == 1

    def remover(self, cpf: str) -> bool:
        cur = self.conn.execute(sql_de("func_remover"), {"cpf": cpf})
        return cur.fetchone() is not None
