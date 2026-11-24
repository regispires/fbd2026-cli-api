from psycopg_pool import ConnectionPool

from empresa.dto import Departamento, DepartamentoAlteracao, DepartamentoNovo
from empresa.erros import NaoEncontrado, ReferenciaInvalida
from empresa.repositorios import DepartamentoRepositorio, FuncionarioRepositorio
from empresa.servicos.base import transacao


class DepartamentoServico:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def criar(self, novo: DepartamentoNovo) -> Departamento:
        with transacao(self.pool) as conn:
            return DepartamentoRepositorio(conn).inserir(novo)

    def obter(self, dnumero: int) -> Departamento:
        with transacao(self.pool) as conn:
            dep = DepartamentoRepositorio(conn).obter(dnumero)
        if dep is None:
            raise NaoEncontrado("departamento", dnumero)
        return dep

    def listar(self) -> list[Departamento]:
        with transacao(self.pool) as conn:
            return DepartamentoRepositorio(conn).listar()

    def renomear(self, dnumero: int, alteracao: DepartamentoAlteracao) -> Departamento:
        with transacao(self.pool) as conn:
            dep = DepartamentoRepositorio(conn).renomear(dnumero, alteracao.dnome)
        if dep is None:
            raise NaoEncontrado("departamento", dnumero)
        return dep

    def remover(self, dnumero: int) -> None:
        try:
            with transacao(self.pool) as conn:
                if not DepartamentoRepositorio(conn).remover(dnumero):
                    raise NaoEncontrado("departamento", dnumero)
        except ReferenciaInvalida as e:
            raise ReferenciaInvalida(
                f"Departamento {dnumero} ainda tem funcionários ou projetos"
            ) from e.__cause__

    def trocar_gerente(self, dnumero: int, cpf: str) -> Departamento:
        """Operação com vários comandos: move o funcionário e o torna gerente."""
        with transacao(self.pool) as conn:
            funcs = FuncionarioRepositorio(conn)
            deps = DepartamentoRepositorio(conn)
            if funcs.obter(cpf) is None:
                raise NaoEncontrado("funcionário", cpf)
            if not deps.definir_gerente(dnumero, cpf):
                raise NaoEncontrado("departamento", dnumero)
            funcs.mudar_departamento(cpf, dnumero)
            return deps.obter(dnumero)
