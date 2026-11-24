"""Serviços: regras de negócio e fronteira das transações.

Cada método obtém uma conexão do pool e abre a transação; os repositórios
usados no mesmo bloco compartilham essa transação.
"""

from psycopg_pool import ConnectionPool

from empresa.servicos.alocacao import AlocacaoServico
from empresa.servicos.departamento import DepartamentoServico
from empresa.servicos.funcionario import FuncionarioServico
from empresa.servicos.projeto import ProjetoServico
from empresa.servicos.relatorio import RelatorioServico


class Servicos:
    """Ponto único de montagem, usado pela CLI e pela API."""

    def __init__(self, pool: ConnectionPool):
        self.funcionarios = FuncionarioServico(pool)
        self.departamentos = DepartamentoServico(pool)
        self.projetos = ProjetoServico(pool)
        self.alocacoes = AlocacaoServico(pool)
        self.relatorios = RelatorioServico(pool)


__all__ = [
    "AlocacaoServico",
    "DepartamentoServico",
    "FuncionarioServico",
    "ProjetoServico",
    "RelatorioServico",
    "Servicos",
]
