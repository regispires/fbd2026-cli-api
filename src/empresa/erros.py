"""Exceções de domínio, independentes do driver, e tradução dos erros do banco."""

from psycopg import errors


class ErroDominio(Exception): ...


class Duplicidade(ErroDominio): ...


class ReferenciaInvalida(ErroDominio): ...


class DadosInvalidos(ErroDominio): ...


class RegraViolada(ErroDominio): ...


class NaoEncontrado(ErroDominio):
    def __init__(self, recurso: str, chave):
        super().__init__(f"{recurso} não encontrado: {chave}")
        self.recurso, self.chave = recurso, chave


# chave: nome da restrição no DDL (sql/01_esquema.sql)
MENSAGENS = {
    "funcionario_pkey": "Já existe funcionário com este CPF",
    "ck_func_cpf": "CPF deve ter 11 dígitos",
    "ck_func_sexo": "Sexo deve ser M ou F",
    "ck_func_salario": "Salário deve ser maior que zero",
    "ck_func_superv": "Funcionário não pode supervisionar a si mesmo",
    "fk_func_superv": "Supervisor informado não existe",
    "fk_func_dep": "Departamento informado não existe",
    "departamento_pkey": "Já existe departamento com este número",
    "departamento_dnome_key": "Nome de departamento já usado",
    "fk_dep_gerente": "Gerente informado não existe",
    "projeto_pkey": "Já existe projeto com este número",
    "projeto_projnome_key": "Nome de projeto já usado",
    "fk_proj_dep": "Departamento informado não existe",
    "trabalha_em_pkey": "Funcionário já alocado no projeto",
    "trabalha_em_fcpf_fkey": "Funcionário informado não existe",
    "trabalha_em_pnr_fkey": "Projeto informado não existe",
    "trabalha_em_horas_check": "Horas devem ser maiores que zero",
}


def traduzir(e: errors.Error) -> ErroDominio:
    """Converte IntegrityError ou DataError em exceção de domínio."""
    if isinstance(e, errors.DataError):
        return DadosInvalidos("Dado inválido: " + (e.diag.message_primary or str(e)))
    nome = e.diag.constraint_name or ""
    msg = MENSAGENS.get(nome, "Operação viola uma regra do banco")
    if isinstance(e, errors.UniqueViolation):
        return Duplicidade(msg)
    if isinstance(e, errors.ForeignKeyViolation):
        return ReferenciaInvalida(msg)
    return DadosInvalidos(msg)
