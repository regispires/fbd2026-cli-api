from decimal import Decimal

from psycopg import Connection, errors
from psycopg_pool import ConnectionPool

from empresa.dto import (
    AlocacaoDetalhe,
    AlocacaoNova,
    FuncionarioRef,
    Rejeicao,
    ResultadoEquipe,
)
from empresa.erros import ErroDominio, NaoEncontrado, RegraViolada, traduzir
from empresa.repositorios import AlocacaoRepositorio, FuncionarioRepositorio
from empresa.servicos.base import id_funcionario, transacao

LIMITE_SEMANAL = Decimal("40")


def _alocar(conn: Connection, ref: FuncionarioRef, projeto_id: int, horas: Decimal) -> None:
    """Leitura, verificação e escrita na mesma transação.

    FOR UPDATE na linha do funcionário serializa alocações concorrentes dele:
    a soma das horas não muda entre a leitura e o INSERT.
    """
    fid = id_funcionario(conn, ref)
    FuncionarioRepositorio(conn).bloquear(fid)
    alocs = AlocacaoRepositorio(conn)
    total = alocs.carga_semanal(fid)
    if total + horas > LIMITE_SEMANAL:
        raise RegraViolada(
            f"Carga semanal do funcionário ({ref.descricao()}) passaria de "
            f"{LIMITE_SEMANAL} h (atual: {total} h)"
        )
    alocs.inserir(fid, projeto_id, horas)


class AlocacaoServico:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def alocar(self, nova: AlocacaoNova) -> None:
        with transacao(self.pool) as conn:
            _alocar(conn, nova.funcionario, nova.projeto_id, nova.horas)

    def alocar_equipe(self, projeto_id: int, equipe: list[AlocacaoNova]) -> ResultadoEquipe:
        """Cada membro num SAVEPOINT: a falha de um não desfaz os outros."""
        alocados, rejeitados = [], []
        with transacao(self.pool) as conn:  # BEGIN
            for membro in equipe:
                quem = membro.funcionario.descricao()
                try:
                    with conn.transaction():  # SAVEPOINT
                        _alocar(conn, membro.funcionario, projeto_id, membro.horas)
                    alocados.append(quem)
                except (errors.IntegrityError, errors.DataError) as e:  # ROLLBACK TO
                    rejeitados.append(Rejeicao(quem, str(traduzir(e))))
                except ErroDominio as e:
                    rejeitados.append(Rejeicao(quem, str(e)))
        return ResultadoEquipe(alocados, rejeitados)  # COMMIT acima

    def remover(self, ref: FuncionarioRef, projeto_id: int) -> None:
        with transacao(self.pool) as conn:
            fid = id_funcionario(conn, ref)
            if not AlocacaoRepositorio(conn).remover(fid, projeto_id):
                raise NaoEncontrado("alocação", f"{ref.descricao()} no projeto {projeto_id}")

    def por_projeto(self, projeto_id: int) -> list[AlocacaoDetalhe]:
        with transacao(self.pool) as conn:
            return AlocacaoRepositorio(conn).por_projeto(projeto_id)
