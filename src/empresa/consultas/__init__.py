"""Consultas SQL centralizadas em arquivos .sql deste pacote."""

from functools import cache
from importlib.resources import files


@cache
def sql_de(nome: str) -> str:
    # lê empresa/consultas/<nome>.sql uma única vez
    arq = files(__package__).joinpath(nome + ".sql")
    return arq.read_text(encoding="utf-8")
