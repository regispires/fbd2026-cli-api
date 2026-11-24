"""Configuração lida do ambiente.

A libpq lê PGHOST, PGPORT, PGDATABASE, PGUSER e PGPASSWORD sozinha quando a
conninfo omite esses parâmetros. Em desenvolvimento, o uv injeta o .env:

    uv run --env-file .env empresa ...
"""

import os
from dataclasses import dataclass

from psycopg.conninfo import make_conninfo


@dataclass(frozen=True)
class Config:
    conninfo: str
    pool_max: int = 10


def carregar() -> Config:
    obrig = ("PGHOST", "PGDATABASE", "PGUSER")
    faltando = [v for v in obrig if v not in os.environ]
    if faltando:
        raise SystemExit("Variáveis ausentes: " + ", ".join(faltando))
    conninfo = make_conninfo(
        application_name="empresa-app",
        connect_timeout=os.getenv("PGCONNECT_TIMEOUT", "5"),
    )
    return Config(conninfo, int(os.getenv("POOL_MAX", "10")))
