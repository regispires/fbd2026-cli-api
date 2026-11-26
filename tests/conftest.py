"""Fixtures de teste contra um PostgreSQL real.

Usa as mesmas variáveis PG* da aplicação. Cria um banco descartável com o
esquema e as visões (as mesmas funções de `empresa banco criar`), recarrega os
dados de exemplo antes de cada teste de serviço (`empresa banco povoar
--limpar`) e remove o banco ao final. O usuário precisa poder criar bancos
(o usuário do docker compose pode).

    uv run pytest
"""

import os
import uuid

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from empresa import banco
from empresa.config import carregar
from empresa.db import criar_pool
from empresa.servicos import Servicos


@pytest.fixture(scope="session")
def banco_descartavel():
    """Fábrica de bancos vazios, removidos ao fim da sessão."""
    adm = carregar().conninfo
    criados = []

    def novo() -> str:
        nome = "empresa_teste_" + uuid.uuid4().hex[:8]
        banco.criar_banco(adm, nome)
        criados.append(nome)
        return nome

    yield novo
    with psycopg.connect(adm, dbname="postgres", autocommit=True) as c:
        for nome in criados:
            c.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(nome))
            )


@pytest.fixture(scope="session")
def banco_teste(banco_descartavel):
    nome = banco_descartavel()
    original = os.environ.get("PGDATABASE")
    os.environ["PGDATABASE"] = nome
    banco.criar_esquema(carregar().conninfo)
    yield nome
    if original is None:
        os.environ.pop("PGDATABASE", None)
    else:
        os.environ["PGDATABASE"] = original


@pytest.fixture(scope="session")
def pool(banco_teste):
    p = criar_pool(min_size=1)
    yield p
    p.close()


@pytest.fixture
def dados(banco_teste):
    """Volta o banco ao estado dos dados de exemplo."""
    banco.povoar(carregar().conninfo, limpar=True)


@pytest.fixture
def servicos(pool, dados) -> Servicos:
    return Servicos(pool)


@pytest.fixture
def conn(pool, dados):
    """Conexão numa transação revertida ao fim do teste (testes de repositório)."""
    with pool.connection() as c:
        with c.transaction(force_rollback=True):
            yield c


@pytest.fixture
def conninfo_vazio(banco_descartavel) -> str:
    """Conninfo de um banco novo, sem esquema (testes de criação do banco)."""
    return make_conninfo(carregar().conninfo, dbname=banco_descartavel())
