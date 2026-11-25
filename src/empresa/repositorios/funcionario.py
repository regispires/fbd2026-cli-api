from decimal import Decimal

from psycopg import Connection, sql
from psycopg.rows import class_row

from empresa.consultas import sql_de
from empresa.dto import Funcionario, FuncionarioNovo, FuncionarioResumo
from empresa.erros import DadosInvalidos
from empresa.validacao import escapar_like

# lista branca de colunas atualizáveis
EDITAVEIS = frozenset({"endereco", "salario", "departamento_id", "supervisor_id"})


class FuncionarioRepositorio:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.rf = class_row(Funcionario)

    def inserir(self, f: FuncionarioNovo, supervisor_id: int | None) -> Funcionario:
        params = f.model_dump(exclude={"supervisor"}) | {"supervisor_id": supervisor_id}
        with self.conn.cursor(row_factory=self.rf) as cur:
            cur.execute(sql_de("func_inserir"), params)
            return cur.fetchone()

    def obter(self, id: int) -> Funcionario | None:
        with self.conn.cursor(row_factory=self.rf) as cur:
            cur.execute(sql_de("func_por_id"), {"id": id})
            return cur.fetchone()

    def obter_por_cpf(self, cpf: str) -> Funcionario | None:
        with self.conn.cursor(row_factory=self.rf) as cur:
            cur.execute(sql_de("func_por_cpf"), {"cpf": cpf})
            return cur.fetchone()

    def id_por_cpf(self, cpf: str) -> int | None:
        linha = self.conn.execute(sql_de("func_id_por_cpf"), {"cpf": cpf}).fetchone()
        return None if linha is None else linha[0]

    def bloquear(self, id: int) -> bool:
        cur = self.conn.execute(sql_de("func_bloquear"), {"id": id})
        return cur.fetchone() is not None

    def buscar(
        self,
        *,
        departamento_id: int | None = None,
        nome: str | None = None,
        salario_min: Decimal | None = None,
        limite: int = 20,
        offset: int = 0,
    ) -> list[FuncionarioResumo]:
        """Filtros opcionais compostos com sql.SQL; valores sempre como parâmetros."""
        conds = []
        p = {"lim": limite, "off": offset}
        if departamento_id is not None:
            conds.append(sql.SQL("departamento_id = %(dep)s"))
            p["dep"] = departamento_id
        if salario_min is not None:
            conds.append(sql.SQL("salario >= %(smin)s"))
            p["smin"] = salario_min
        if nome:
            conds.append(sql.SQL("nome ILIKE %(nome)s"))
            p["nome"] = "%" + escapar_like(nome) + "%"
        where = sql.SQL(" AND ").join(conds) if conds else sql.SQL("TRUE")
        q = sql.SQL(
            "SELECT id, cpf, nome, departamento_id, dnome, salario"
            "  FROM vw_funcionario_depto WHERE {}"
            " ORDER BY nome, id LIMIT %(lim)s OFFSET %(off)s"
        ).format(where)
        with self.conn.cursor(row_factory=class_row(FuncionarioResumo)) as cur:
            return cur.execute(q, p).fetchall()

    def atualizar(self, id: int, mudancas: dict) -> Funcionario | None:
        if not mudancas or mudancas.keys() - EDITAVEIS:
            raise DadosInvalidos("Campos inválidos para atualização")
        sets = sql.SQL(", ").join(
            sql.SQL("{} = {}").format(sql.Identifier(c), sql.Placeholder(c)) for c in mudancas
        )
        q = sql.SQL(
            "UPDATE funcionario SET {} WHERE id = %(id)s"
            " RETURNING id, cpf, pnome, minicial, unome, datanasc, endereco,"
            " sexo, salario, supervisor_id, departamento_id"
        ).format(sets)
        with self.conn.cursor(row_factory=self.rf) as cur:
            return cur.execute(q, {**mudancas, "id": id}).fetchone()

    def mudar_departamento(self, id: int, departamento_id: int) -> bool:
        cur = self.conn.execute(
            sql_de("func_mudar_dep"), {"id": id, "departamento_id": departamento_id}
        )
        return cur.rowcount == 1

    def remover(self, id: int) -> bool:
        cur = self.conn.execute(sql_de("func_remover"), {"id": id})
        return cur.fetchone() is not None
