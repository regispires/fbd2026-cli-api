from pathlib import Path

from psycopg_pool import ConnectionPool

from empresa.dto import FuncionarioDepartamento, PosicaoSalarial, ResumoDepartamento
from empresa.erros import NaoEncontrado
from empresa.repositorios import DepartamentoRepositorio, RelatorioRepositorio
from empresa.servicos.base import transacao


class RelatorioServico:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def departamentos(self) -> list[ResumoDepartamento]:
        with transacao(self.pool) as conn:
            return RelatorioRepositorio(conn).departamentos()

    def ranking(self, deps: list[int] | None = None) -> list[PosicaoSalarial]:
        with transacao(self.pool) as conn:
            if not deps:
                deps = [d.dnumero for d in DepartamentoRepositorio(conn).listar()]
            return RelatorioRepositorio(conn).ranking(deps)

    def todos_projetos(self) -> list[FuncionarioDepartamento]:
        with transacao(self.pool) as conn:
            return RelatorioRepositorio(conn).todos_projetos()

    def supervisao(self, cpf_raiz: str) -> dict:
        """Linhas planas do banco viram uma árvore de dicionários."""
        with transacao(self.pool) as conn:
            linhas = RelatorioRepositorio(conn).supervisao(cpf_raiz)
        if not linhas:
            raise NaoEncontrado("funcionário", cpf_raiz)
        filhos: dict[str, list[tuple[str, str]]] = {}
        for cpf, nome, sup in linhas[1:]:
            filhos.setdefault(sup, []).append((cpf, nome))

        def montar(cpf: str, nome: str) -> dict:
            equipe = [montar(*f) for f in filhos.get(cpf, [])]
            return {"cpf": cpf, "nome": nome, "equipe": equipe}

        return montar(linhas[0][0], linhas[0][1])

    def exportar_csv(self, caminho: Path) -> int:
        with transacao(self.pool) as conn, open(caminho, "w", newline="", encoding="utf-8") as arq:
            return RelatorioRepositorio(conn).exportar_csv(arq)
