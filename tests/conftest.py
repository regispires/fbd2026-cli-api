"""Fixtures de teste contra um PostgreSQL real.

Usa as mesmas variáveis PG* da aplicação. Cria um banco descartável com o
esquema e as visões, recarrega os dados de exemplo antes de cada teste de
serviço e remove o banco ao final. O usuário precisa poder criar bancos
(o usuário do docker compose pode).

    uv run --env-file .env pytest
"""

import os
import pathlib
import uuid

import psycopg
import pytest
from psycopg import sql

from empresa.db import criar_pool
from empresa.servicos import Servicos

RAIZ = pathlib.Path(__file__).resolve().parents[1]
ESTRUTURA = [RAIZ / "sql" / "01_esquema.sql", RAIZ / "sql" / "02_visoes.sql"]
DADOS = RAIZ / "sql" / "03_dados_exemplo.sql"


def executar_script(caminho: pathlib.Path) -> None:
    # sem parâmetros, o Psycopg aceita vários comandos numa só execução
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(caminho.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def banco_teste():
    nome = "empresa_teste_" + uuid.uuid4().hex[:8]
    with psycopg.connect("", autocommit=True) as adm:
        adm.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(nome)))
    original = os.environ.get("PGDATABASE")
    os.environ["PGDATABASE"] = nome
    try:
        for script in ESTRUTURA:
            executar_script(script)
        yield nome
    finally:
        if original is None:
            os.environ.pop("PGDATABASE", None)
        else:
            os.environ["PGDATABASE"] = original
        with psycopg.connect("", autocommit=True) as adm:
            adm.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(nome))
            )


@pytest.fixture(scope="session")
def pool(banco_teste):
    p = criar_pool(min_size=1)
    yield p
    p.close()


@pytest.fixture
def dados(banco_teste):
    """Volta o banco ao estado dos dados de exemplo."""
    with psycopg.connect("", autocommit=True) as conn:
        conn.execute(
            "TRUNCATE dependente, trabalha_em, localizacoes_dep, projeto,"
            " departamento, funcionario RESTART IDENTITY CASCADE"
        )
    executar_script(DADOS)


@pytest.fixture
def servicos(pool, dados) -> Servicos:
    return Servicos(pool)


@pytest.fixture
def conn(pool, dados):
    """Conexão numa transação revertida ao fim do teste (testes de repositório)."""
    with pool.connection() as c:
        with c.transaction(force_rollback=True):
            yield c
