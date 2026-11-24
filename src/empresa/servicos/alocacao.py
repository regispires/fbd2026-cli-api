from decimal import Decimal

from psycopg import Connection, errors
from psycopg_pool import ConnectionPool

from empresa.dto import AlocacaoDetalhe, AlocacaoNova, Rejeicao, ResultadoEquipe
from empresa.erros import ErroDominio, NaoEncontrado, RegraViolada, traduzir
from empresa.repositorios import AlocacaoRepositorio, FuncionarioRepositorio
from empresa.servicos.base import transacao

LIMITE_SEMANAL = Decimal("40")


def _alocar(conn: Connection, cpf: str, projnumero: int, horas: Decimal) -> None:
    """Leitura, verificação e escrita na mesma transação.

    FOR UPDATE na linha do funcionário serializa alocações concorrentes dele:
    a soma das horas não muda entre a leitura e o INSERT.
    """
    if not FuncionarioRepositorio(conn).bloquear(cpf):
        raise NaoEncontrado("funcionário", cpf)
    alocs = AlocacaoRepositorio(conn)
    total = alocs.carga_semanal(cpf)
    if total + horas > LIMITE_SEMANAL:
        raise RegraViolada(
            f"Carga semanal de {cpf} passaria de {LIMITE_SEMANAL} h (atual: {total} h)"
        )
    alocs.inserir(cpf, projnumero, horas)


class AlocacaoServico:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def alocar(self, nova: AlocacaoNova) -> None:
        with transacao(self.pool) as conn:
            _alocar(conn, nova.cpf, nova.projnumero, nova.horas)

    def alocar_equipe(self, projnumero: int, equipe: list[AlocacaoNova]) -> ResultadoEquipe:
        """Cada membro num SAVEPOINT: a falha de um não desfaz os outros."""
        alocados, rejeitados = [], []
        with transacao(self.pool) as conn:  # BEGIN
            for membro in equipe:
                try:
                    with conn.transaction():  # SAVEPOINT
                        _alocar(conn, membro.cpf, projnumero, membro.horas)
                    alocados.append(membro.cpf)
                except (errors.IntegrityError, errors.DataError) as e:  # ROLLBACK TO
                    rejeitados.append(Rejeicao(membro.cpf, str(traduzir(e))))
                except ErroDominio as e:
                    rejeitados.append(Rejeicao(membro.cpf, str(e)))
        return ResultadoEquipe(alocados, rejeitados)  # COMMIT acima

    def remover(self, cpf: str, projnumero: int) -> None:
        with transacao(self.pool) as conn:
            if not AlocacaoRepositorio(conn).remover(cpf, projnumero):
                raise NaoEncontrado("alocação", f"{cpf} no projeto {projnumero}")

    def por_projeto(self, projnumero: int) -> list[AlocacaoDetalhe]:
        with transacao(self.pool) as conn:
            return AlocacaoRepositorio(conn).por_projeto(projnumero)
