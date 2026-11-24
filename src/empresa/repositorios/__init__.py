"""Repositórios: só SQL e mapeamento. Recebem a conexão pronta; não abrem
conexão, não fazem COMMIT e não contêm regra de negócio."""

from empresa.repositorios.alocacao import AlocacaoRepositorio
from empresa.repositorios.departamento import DepartamentoRepositorio
from empresa.repositorios.funcionario import FuncionarioRepositorio
from empresa.repositorios.projeto import ProjetoRepositorio
from empresa.repositorios.relatorio import RelatorioRepositorio

__all__ = [
    "AlocacaoRepositorio",
    "DepartamentoRepositorio",
    "FuncionarioRepositorio",
    "ProjetoRepositorio",
    "RelatorioRepositorio",
]
