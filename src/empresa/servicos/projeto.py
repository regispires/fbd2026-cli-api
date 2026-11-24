from psycopg_pool import ConnectionPool

from empresa.dto import Projeto, ProjetoAlteracao, ProjetoNovo
from empresa.erros import DadosInvalidos, NaoEncontrado, ReferenciaInvalida
from empresa.repositorios import ProjetoRepositorio
from empresa.servicos.base import transacao


class ProjetoServico:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def criar(self, novo: ProjetoNovo) -> Projeto:
        with transacao(self.pool) as conn:
            return ProjetoRepositorio(conn).inserir(novo)

    def obter(self, projnumero: int) -> Projeto:
        with transacao(self.pool) as conn:
            proj = ProjetoRepositorio(conn).obter(projnumero)
        if proj is None:
            raise NaoEncontrado("projeto", projnumero)
        return proj

    def listar(self, dnum: int | None = None) -> list[Projeto]:
        with transacao(self.pool) as conn:
            return ProjetoRepositorio(conn).listar(dnum)

    def atualizar(self, projnumero: int, alteracao: ProjetoAlteracao) -> Projeto:
        mudancas = alteracao.model_dump(exclude_unset=True)
        if not mudancas:
            raise DadosInvalidos("Informe ao menos um campo para atualizar")
        with transacao(self.pool) as conn:
            proj = ProjetoRepositorio(conn).atualizar(projnumero, mudancas)
        if proj is None:
            raise NaoEncontrado("projeto", projnumero)
        return proj

    def remover(self, projnumero: int) -> None:
        try:
            with transacao(self.pool) as conn:
                if not ProjetoRepositorio(conn).remover(projnumero):
                    raise NaoEncontrado("projeto", projnumero)
        except ReferenciaInvalida as e:
            raise ReferenciaInvalida(
                f"Projeto {projnumero} ainda tem funcionários alocados"
            ) from e.__cause__
