from decimal import Decimal

from psycopg import errors
from psycopg_pool import ConnectionPool

from empresa.dto import (
    Funcionario,
    FuncionarioAlteracao,
    FuncionarioNovo,
    FuncionarioRef,
    FuncionarioResumo,
)
from empresa.erros import DadosInvalidos, NaoEncontrado, ReferenciaInvalida
from empresa.repositorios import FuncionarioRepositorio
from empresa.servicos.base import id_funcionario, transacao

LIMITE_MAXIMO = 100


class FuncionarioServico:
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def criar(self, novo: FuncionarioNovo) -> Funcionario:
        with transacao(self.pool) as conn:
            sup = None if novo.supervisor is None else id_funcionario(conn, novo.supervisor)
            return FuncionarioRepositorio(conn).inserir(novo, sup)

    def obter(self, ref: FuncionarioRef) -> Funcionario:
        with transacao(self.pool) as conn:
            repo = FuncionarioRepositorio(conn)
            func = repo.obter(ref.id) if ref.id is not None else repo.obter_por_cpf(ref.cpf)
        if func is None:
            raise NaoEncontrado("funcionário", ref.descricao())
        return func

    def listar(
        self,
        *,
        departamento_id: int | None = None,
        nome: str | None = None,
        salario_min: Decimal | None = None,
        limite: int = 20,
        pagina: int = 1,
    ) -> list[FuncionarioResumo]:
        if not 1 <= limite <= LIMITE_MAXIMO or pagina < 1:
            raise DadosInvalidos(f"Use limite entre 1 e {LIMITE_MAXIMO} e página a partir de 1")
        with transacao(self.pool) as conn:
            return FuncionarioRepositorio(conn).buscar(
                departamento_id=departamento_id,
                nome=nome,
                salario_min=salario_min,
                limite=limite,
                offset=(pagina - 1) * limite,
            )

    def atualizar(self, ref: FuncionarioRef, alteracao: FuncionarioAlteracao) -> Funcionario:
        mudancas = alteracao.model_dump(exclude_unset=True, exclude={"supervisor"})
        informou_supervisor = "supervisor" in alteracao.model_fields_set
        if not mudancas and not informou_supervisor:
            raise DadosInvalidos("Informe ao menos um campo para atualizar")
        with transacao(self.pool) as conn:
            fid = id_funcionario(conn, ref)
            if informou_supervisor:
                sup = alteracao.supervisor
                mudancas["supervisor_id"] = None if sup is None else id_funcionario(conn, sup)
            return FuncionarioRepositorio(conn).atualizar(fid, mudancas)

    def remover(self, ref: FuncionarioRef) -> None:
        try:
            with transacao(self.pool) as conn:
                FuncionarioRepositorio(conn).remover(id_funcionario(conn, ref))
        except ReferenciaInvalida as e:
            # gerente de departamento ou alocado em projeto
            causa = e.__cause__
            tabela = causa.diag.table_name if isinstance(causa, errors.Error) else None
            raise ReferenciaInvalida(
                f"Funcionário ({ref.descricao()}) ainda é referenciado em "
                f"{tabela or 'outra tabela'}"
            ) from causa
