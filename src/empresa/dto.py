"""Objetos de transferência de dados.

Entrada: modelos Pydantic, validados ao serem construídos (CLI e API usam os mesmos).
Saída: dataclasses preenchidas por class_row, sem revalidar o que o banco garante.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from empresa.validacao import normalizar_cpf, validar_cpf

ENTRADA = ConfigDict(frozen=True, str_strip_whitespace=True)

Nome = Annotated[str, Field(min_length=1, max_length=15)]
Salario = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
Horas = Annotated[Decimal, Field(gt=0, max_digits=4, decimal_places=1)]
NomeLongo = Annotated[str, Field(min_length=1, max_length=30)]


def _cpf_referencia(v: str | None) -> str | None:
    # CPF de funcionário já cadastrado: só formato; o banco confere a existência
    return None if v is None else normalizar_cpf(v)


# ------------------------------------------------------------------ entrada
class FuncionarioNovo(BaseModel):
    model_config = ENTRADA
    cpf: str
    pnome: Nome
    unome: Nome
    salario: Salario
    dnr: int
    minicial: Annotated[str | None, Field(max_length=1)] = None
    endereco: Annotated[str | None, Field(max_length=60)] = None
    datanasc: date | None = None
    sexo: Literal["M", "F"] | None = None
    cpf_supervisor: str | None = None

    @field_validator("cpf")
    @classmethod
    def cpf_valido(cls, v: str) -> str:
        return validar_cpf(v)

    @field_validator("cpf_supervisor")
    @classmethod
    def supervisor_valido(cls, v: str | None) -> str | None:
        return _cpf_referencia(v)


class FuncionarioAlteracao(BaseModel):
    """Atualização parcial: model_dump(exclude_unset=True) traz só o informado."""

    model_config = ENTRADA
    endereco: Annotated[str | None, Field(max_length=60)] = None
    salario: Salario | None = None
    dnr: int | None = None
    cpf_supervisor: str | None = None

    @field_validator("cpf_supervisor")
    @classmethod
    def supervisor_valido(cls, v: str | None) -> str | None:
        return _cpf_referencia(v)


class DepartamentoNovo(BaseModel):
    model_config = ENTRADA
    dnumero: Annotated[int, Field(gt=0)]
    dnome: NomeLongo


class DepartamentoAlteracao(BaseModel):
    model_config = ENTRADA
    dnome: NomeLongo


class GerenteNovo(BaseModel):
    model_config = ENTRADA
    cpf: str

    @field_validator("cpf")
    @classmethod
    def cpf_valido(cls, v: str) -> str:
        return normalizar_cpf(v)


class ProjetoNovo(BaseModel):
    model_config = ENTRADA
    projnome: NomeLongo
    dnum: int
    projlocal: Annotated[str | None, Field(max_length=30)] = None


class ProjetoAlteracao(BaseModel):
    model_config = ENTRADA
    projnome: NomeLongo | None = None
    projlocal: Annotated[str | None, Field(max_length=30)] = None
    dnum: int | None = None


class AlocacaoNova(BaseModel):
    model_config = ENTRADA
    cpf: str
    projnumero: int
    horas: Horas

    @field_validator("cpf")
    @classmethod
    def cpf_valido(cls, v: str) -> str:
        return normalizar_cpf(v)


# ------------------------------------------------------------------ saída
@dataclass(frozen=True, slots=True)
class Funcionario:
    cpf: str
    pnome: str
    minicial: str | None
    unome: str
    datanasc: date | None
    endereco: str | None
    sexo: str | None
    salario: Decimal
    cpf_supervisor: str | None
    dnr: int | None

    @property
    def nome(self) -> str:
        partes = (self.pnome, self.minicial, self.unome)
        return " ".join(p for p in partes if p)


@dataclass(frozen=True, slots=True)
class FuncionarioResumo:
    cpf: str
    nome: str
    dnumero: int
    dnome: str
    salario: Decimal


@dataclass(frozen=True, slots=True)
class Departamento:
    dnumero: int
    dnome: str
    cpf_gerente: str | None
    data_inicio_gerente: date | None


@dataclass(frozen=True, slots=True)
class Projeto:
    projnumero: int
    projnome: str
    projlocal: str | None
    dnum: int


@dataclass(frozen=True, slots=True)
class AlocacaoDetalhe:
    cpf: str
    nome: str
    projnumero: int
    projnome: str
    horas: Decimal


@dataclass(frozen=True, slots=True)
class Rejeicao:
    cpf: str
    motivo: str


@dataclass(frozen=True, slots=True)
class ResultadoEquipe:
    alocados: list[str]
    rejeitados: list[Rejeicao]


# ------------------------------------------------------------------ relatórios
@dataclass(frozen=True, slots=True)
class ResumoDepartamento:
    dnumero: int
    dnome: str
    qtd_func: int
    folha: Decimal
    media: Decimal | None
    qtd_proj: int


@dataclass(frozen=True, slots=True)
class PosicaoSalarial:
    dnome: str
    nome: str
    salario: Decimal
    posicao: int
    dif_media: Decimal


@dataclass(frozen=True, slots=True)
class FuncionarioDepartamento:
    cpf: str
    nome: str
    dnome: str
