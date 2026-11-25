from psycopg_pool import ConnectionPool

from empresa.dto import Departamento, DepartamentoAlteracao, DepartamentoNovo, FuncionarioRef
from empresa.erros import NaoEncontrado, ReferenciaInvalida
from empresa.repositorios import DepartamentoRepositorio, FuncionarioRepositorio
from empresa.servicos.base import id_funcionario, transacao


class DepartamentoServico:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def criar(self, novo: DepartamentoNovo) -> Departamento:
        with transacao(self.pool) as conn:
            return DepartamentoRepositorio(conn).inserir(novo)

    def obter(self, id: int) -> Departamento:
        with transacao(self.pool) as conn:
            dep = DepartamentoRepositorio(conn).obter(id)
        if dep is None:
            raise NaoEncontrado("departamento", id)
        return dep

    def listar(self) -> list[Departamento]:
        with transacao(self.pool) as conn:
            return DepartamentoRepositorio(conn).listar()

    def renomear(self, id: int, alteracao: DepartamentoAlteracao) -> Departamento:
        with transacao(self.pool) as conn:
            dep = DepartamentoRepositorio(conn).renomear(id, alteracao.dnome)
        if dep is None:
            raise NaoEncontrado("departamento", id)
        return dep

    def remover(self, id: int) -> None:
        try:
            with transacao(self.pool) as conn:
                if not DepartamentoRepositorio(conn).remover(id):
                    raise NaoEncontrado("departamento", id)
        except ReferenciaInvalida as e:
            raise ReferenciaInvalida(
                f"Departamento {id} ainda tem funcionários ou projetos"
            ) from e.__cause__

    def trocar_gerente(self, id: int, gerente: FuncionarioRef) -> Departamento:
        """Operação com vários comandos: move o funcionário e o torna gerente."""
        with transacao(self.pool) as conn:
            fid = id_funcionario(conn, gerente)
            deps = DepartamentoRepositorio(conn)
            if not deps.definir_gerente(id, fid):
                raise NaoEncontrado("departamento", id)
            FuncionarioRepositorio(conn).mudar_departamento(fid, id)
            return deps.obter(id)
