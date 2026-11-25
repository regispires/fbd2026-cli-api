from pathlib import Path

from psycopg_pool import ConnectionPool

from empresa.dto import (
    DependentesFuncionario,
    EquipeProjeto,
    FuncionarioDepartamento,
    FuncionarioRef,
    PosicaoSalarial,
    ResumoDepartamento,
)
from empresa.erros import DadosInvalidos
from empresa.repositorios import DepartamentoRepositorio, RelatorioRepositorio
from empresa.servicos.base import id_funcionario, transacao


class RelatorioServico:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def departamentos(self) -> list[ResumoDepartamento]:
        with transacao(self.pool) as conn:
            return RelatorioRepositorio(conn).departamentos()

    def ranking(self, deps: list[int] | None = None) -> list[PosicaoSalarial]:
        with transacao(self.pool) as conn:
            if not deps:
                deps = [d.id for d in DepartamentoRepositorio(conn).listar()]
            return RelatorioRepositorio(conn).ranking(deps)

    def todos_projetos(self) -> list[FuncionarioDepartamento]:
        with transacao(self.pool) as conn:
            return RelatorioRepositorio(conn).todos_projetos()

    def equipes(self, max_func: int) -> list[EquipeProjeto]:
        if max_func < 0:
            raise DadosInvalidos("o número máximo de funcionários não pode ser negativo")
        with transacao(self.pool) as conn:
            return RelatorioRepositorio(conn).equipes(max_func)

    def dependentes(self, min_dep: int = 0) -> list[DependentesFuncionario]:
        if min_dep < 0:
            raise DadosInvalidos("o número mínimo de dependentes não pode ser negativo")
        with transacao(self.pool) as conn:
            return RelatorioRepositorio(conn).dependentes(min_dep)

    def supervisao(self, raiz: FuncionarioRef) -> dict:
        """Linhas planas do banco viram uma árvore de dicionários."""
        with transacao(self.pool) as conn:
            linhas = RelatorioRepositorio(conn).supervisao(id_funcionario(conn, raiz))
        filhos: dict[int, list[tuple[int, str, str]]] = {}
        for fid, cpf, nome, sup in linhas[1:]:
            filhos.setdefault(sup, []).append((fid, cpf, nome))

        def montar(fid: int, cpf: str, nome: str) -> dict:
            equipe = [montar(*f) for f in filhos.get(fid, [])]
            return {"id": fid, "cpf": cpf, "nome": nome, "equipe": equipe}

        fid, cpf, nome, _ = linhas[0]
        return montar(fid, cpf, nome)

    def exportar_csv(self, caminho: Path) -> int:
        with transacao(self.pool) as conn, open(caminho, "w", newline="", encoding="utf-8") as arq:
            return RelatorioRepositorio(conn).exportar_csv(arq)
