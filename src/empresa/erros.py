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
    "uq_func_cpf": "Já existe funcionário com este CPF",
    "ck_func_cpf": "CPF deve ter 11 dígitos",
    "ck_func_sexo": "Sexo deve ser M ou F",
    "ck_func_salario": "Salário deve ser maior que zero",
    "ck_func_superv": "Funcionário não pode supervisionar a si mesmo",
    "fk_func_superv": "Supervisor informado não existe",
    "fk_func_dep": "Departamento informado não existe",
    "uq_dep_nome": "Nome de departamento já usado",
    "fk_dep_gerente": "Gerente informado não existe",
    "uq_proj_nome": "Nome de projeto já usado",
    "fk_proj_dep": "Departamento informado não existe",
    "pk_trabalha_em": "Funcionário já alocado no projeto",
    "fk_te_func": "Funcionário informado não existe",
    "fk_te_proj": "Projeto informado não existe",
    "ck_te_horas": "Horas devem ser maiores que zero",
    "uq_dependente": "Funcionário já tem dependente com este nome",
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
