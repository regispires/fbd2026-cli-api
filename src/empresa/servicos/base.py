from collections.abc import Iterator
from contextlib import contextmanager

from psycopg import Connection, errors
from psycopg_pool import ConnectionPool

from empresa.dto import FuncionarioRef
from empresa.erros import NaoEncontrado, traduzir
from empresa.repositorios import FuncionarioRepositorio


@contextmanager
def transacao(pool: ConnectionPool) -> Iterator[Connection]:
    """Empresta uma conexão do pool e abre uma transação.

    COMMIT na saída normal; ROLLBACK em qualquer exceção. Violações de
    integridade e dados inválidos viram exceções de domínio.
    """
    try:
        with pool.connection() as conn, conn.transaction():
            yield conn
    except (errors.IntegrityError, errors.DataError) as e:
        raise traduzir(e) from e


def id_funcionario(conn: Connection, ref: FuncionarioRef) -> int:
    """Converte a referência (id ou CPF) no id, conferindo que o funcionário existe."""
    repo = FuncionarioRepositorio(conn)
    if ref.cpf is not None:
        fid = repo.id_por_cpf(ref.cpf)
    else:
        fid = ref.id if repo.obter(ref.id) is not None else None
    if fid is None:
        raise NaoEncontrado("funcionário", ref.descricao())
    return fid
