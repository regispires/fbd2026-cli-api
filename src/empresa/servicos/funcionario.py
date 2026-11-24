from decimal import Decimal

from psycopg import errors
from psycopg_pool import ConnectionPool

from empresa.dto import Funcionario, FuncionarioAlteracao, FuncionarioNovo, FuncionarioResumo
from empresa.erros import DadosInvalidos, NaoEncontrado, ReferenciaInvalida
from empresa.repositorios import FuncionarioRepositorio
from empresa.servicos.base import transacao

LIMITE_MAXIMO = 100


class FuncionarioServico:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def criar(self, novo: FuncionarioNovo) -> Funcionario:
        with transacao(self.pool) as conn:
            return FuncionarioRepositorio(conn).inserir(novo)

    def obter(self, cpf: str) -> Funcionario:
        with transacao(self.pool) as conn:
            func = FuncionarioRepositorio(conn).obter(cpf)
        if func is None:
            raise NaoEncontrado("funcionário", cpf)
        return func

    def listar(
        self,
        *,
        dnr: int | None = None,
        nome: str | None = None,
        salario_min: Decimal | None = None,
        limite: int = 20,
        pagina: int = 1,
    ) -> list[FuncionarioResumo]:
        if not 1 <= limite <= LIMITE_MAXIMO or pagina < 1:
            raise DadosInvalidos(f"Use limite entre 1 e {LIMITE_MAXIMO} e página a partir de 1")
        with transacao(self.pool) as conn:
            return FuncionarioRepositorio(conn).buscar(
                dnr=dnr,
                nome=nome,
                salario_min=salario_min,
                limite=limite,
                offset=(pagina - 1) * limite,
            )

    def atualizar(self, cpf: str, alteracao: FuncionarioAlteracao) -> Funcionario:
        mudancas = alteracao.model_dump(exclude_unset=True)
        if not mudancas:
            raise DadosInvalidos("Informe ao menos um campo para atualizar")
        with transacao(self.pool) as conn:
            func = FuncionarioRepositorio(conn).atualizar(cpf, mudancas)
        if func is None:
            raise NaoEncontrado("funcionário", cpf)
        return func

    def remover(self, cpf: str) -> None:
        try:
            with transacao(self.pool) as conn:
                if not FuncionarioRepositorio(conn).remover(cpf):
                    raise NaoEncontrado("funcionário", cpf)
        except ReferenciaInvalida as e:
            # gerente de departamento ou alocado em projeto
            causa = e.__cause__
            tabela = causa.diag.table_name if isinstance(causa, errors.Error) else None
            raise ReferenciaInvalida(
                f"Funcionário {cpf} ainda é referenciado em {tabela or 'outra tabela'}"
            ) from causa
