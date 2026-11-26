"""Criação do banco, do esquema e carga dos dados de exemplo.

São três passos independentes, para que a aplicação possa começar com ou sem
dados iniciais:

1. criar_banco: cria o banco de dados se ele não existir. CREATE DATABASE não
   pode rodar dentro de uma transação, por isso usa autocommit.
2. criar_esquema: cria tabelas, índices e visões numa única transação. O DDL do
   PostgreSQL é transacional: se um comando falhar, nada fica criado.
3. povoar: carrega os dados de exemplo numa única transação.

Funciona com qualquer servidor indicado pelas variáveis PG*: local, no Docker ou na
nuvem. Na nuvem, o banco costuma já existir, e o passo 1 apenas confirma isso.
"""

from importlib.resources import files

import psycopg
from psycopg import sql

from empresa.erros import RegraViolada

TABELAS = (
    "dependente",
    "trabalha_em",
    "localizacoes_dep",
    "projeto",
    "departamento",
    "funcionario",
)


def script(nome: str) -> str:
    # os scripts ficam em empresa/sql/, empacotados com a aplicação
    return files(__package__).joinpath("sql", nome).read_text(encoding="utf-8")


def criar_banco(conninfo: str, nome: str) -> bool:
    """Cria o banco `nome` se ele não existir. Devolve True se criou."""
    try:
        # caso comum na nuvem: o banco já existe e o usuário nem pode criar outros
        with psycopg.connect(conninfo, dbname=nome):
            return False
    except psycopg.OperationalError as erro_destino:
        try:
            # o banco de manutenção "postgres" existe em qualquer servidor
            adm = psycopg.connect(conninfo, dbname="postgres", autocommit=True)
        except psycopg.OperationalError:
            raise erro_destino from None  # servidor fora do ar, senha errada etc.
        with adm:
            existe = adm.execute("SELECT 1 FROM pg_database WHERE datname = %s", (nome,)).fetchone()
            if existe:
                raise erro_destino from None  # existe, mas a conexão foi recusada
            adm.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(nome)))
            return True


def esquema_existe(conn: psycopg.Connection) -> bool:
    return conn.execute("SELECT to_regclass('funcionario') IS NOT NULL").fetchone()[0]


def criar_esquema(conninfo: str, recriar: bool = False) -> None:
    """Cria tabelas, índices e visões. Tudo ou nada."""
    with psycopg.connect(conninfo) as conn, conn.transaction():
        if esquema_existe(conn):
            if not recriar:
                raise RegraViolada(
                    "O esquema já existe; use --recriar para apagá-lo e criá-lo de novo"
                )
            conn.execute(script("remover.sql"))
        # sem parâmetros, o Psycopg aceita vários comandos numa só execução
        conn.execute(script("01_esquema.sql"))
        conn.execute(script("02_visoes.sql"))


def povoar(conninfo: str, limpar: bool = False) -> int:
    """Carrega os dados de exemplo. Tudo ou nada. Devolve o total de funcionários."""
    with psycopg.connect(conninfo) as conn, conn.transaction():
        if not esquema_existe(conn):
            raise RegraViolada("O esquema não existe; rode antes: empresa banco criar")
        tem_dados = sql.SQL(" OR ").join(
            sql.SQL("EXISTS (SELECT 1 FROM {})").format(sql.Identifier(t)) for t in TABELAS
        )
        if conn.execute(sql.SQL("SELECT ") + tem_dados).fetchone()[0]:
            if not limpar:
                raise RegraViolada(
                    "O banco já tem dados; use --limpar para substituí-los pelos de exemplo"
                )
            conn.execute(script("limpar_dados.sql"))
        conn.execute(script("03_dados_exemplo.sql"))
        return conn.execute("SELECT count(*) FROM funcionario").fetchone()[0]
