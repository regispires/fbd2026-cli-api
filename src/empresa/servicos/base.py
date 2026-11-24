from collections.abc import Iterator
from contextlib import contextmanager

from psycopg import Connection, errors
from psycopg_pool import ConnectionPool

from empresa.erros import traduzir


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
