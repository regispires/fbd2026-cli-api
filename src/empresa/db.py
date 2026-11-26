"""Criação do pool de conexões, compartilhado por CLI e API."""

import atexit

from psycopg_pool import ConnectionPool

from empresa.config import carregar


def criar_pool(min_size: int = 2, espera: float = 10) -> ConnectionPool:
    cfg = carregar()
    pool = ConnectionPool(
        conninfo=cfg.conninfo,
        min_size=min_size,
        max_size=max(min_size, cfg.pool_max),
        max_idle=300,  # segundos ociosa antes de fechar
        timeout=10,  # espera máxima por conexão livre
        check=ConnectionPool.check_connection,
        kwargs={"prepare_threshold": cfg.prepare_threshold},
        open=False,
    )
    pool.open(wait=True, timeout=espera)  # falha cedo se o banco não responder
    atexit.register(pool.close)
    return pool
