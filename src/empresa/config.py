"""Configuração lida do ambiente.

A libpq lê PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD e PGSSLMODE sozinha
quando a conninfo omite esses parâmetros. O mesmo código atende a um banco
local, no Docker ou na nuvem (com PGSSLMODE=require).

Em desenvolvimento, as variáveis vêm do arquivo .env da pasta atual, carregado
por load_dotenv. Variáveis já definidas no ambiente têm prioridade sobre o
arquivo: as do Docker Compose, as de um servidor na nuvem ou as passadas com
`uv run --env-file`.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from psycopg.conninfo import make_conninfo


@dataclass(frozen=True)
class Config:
    conninfo: str
    pool_max: int = 10
    prepare_threshold: int | None = 5  # padrão do Psycopg; None desliga o preparo


def carregar() -> Config:
    # só o .env da pasta atual, sem procurar nas pastas acima; override=False
    # mantém o que já estiver definido no ambiente
    load_dotenv(Path.cwd() / ".env", override=False)
    obrig = ("PGHOST", "PGDATABASE", "PGUSER")
    faltando = [v for v in obrig if v not in os.environ]
    if faltando:
        raise SystemExit("Variáveis ausentes: " + ", ".join(faltando))
    conninfo = make_conninfo(
        application_name="empresa-app",
        connect_timeout=os.getenv("PGCONNECT_TIMEOUT", "5"),
    )
    # poolers em modo transação (comuns na nuvem) não convivem com comandos
    # preparados no servidor: PREPARE_THRESHOLD=off desliga o preparo automático
    limiar = os.getenv("PREPARE_THRESHOLD", "5")
    return Config(
        conninfo,
        int(os.getenv("POOL_MAX", "10")),
        None if limiar.lower() == "off" else int(limiar),
    )
