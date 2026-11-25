"""Objetos de transferência de dados.

Entrada: modelos Pydantic, validados ao serem construídos (CLI e API usam os mesmos).
Saída: dataclasses preenchidas por class_row, sem revalidar o que o banco garante.

Um funcionário pode ser indicado pela chave substituta (id) ou pela chave
natural (CPF): FuncionarioRef aceita exatamente um dos dois.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from empresa.validacao import normalizar_cpf, validar_cpf

ENTRADA = ConfigDict(frozen=True, str_strip_whitespace=True)

Id = Annotated[int, Field(gt=0)]
Nome = Annotated[str, Field(min_length=1, max_length=15)]
Salario = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]
Horas = Annotated[Decimal, Field(gt=0, max_digits=4, decimal_places=1)]
NomeLongo = Annotated[str, Field(min_length=1, max_length=30)]


# ------------------------------------------------------------------ entrada
class FuncionarioRef(BaseModel):
    """Identifica um funcionário já cadastrado por id ou por CPF (exatamente um)."""

    model_config = ENTRADA
    id: Id | None = None
    cpf: str | None = None

    @field_validator("cpf")
    @classmethod
    def cpf_formato(cls, v: str | None) -> str | None:
        # CPF de referência: só o formato; o banco confere a existência
        return None if v is None else normalizar_cpf(v)

    @model_validator(mode="after")
    def um_dos_dois(self) -> "FuncionarioRef":
        if (self.id is None) == (self.cpf is None):
            raise ValueError("informe o id ou o CPF do funcionário (um dos dois)")
        return self

    def descricao(self) -> str:
        return f"id {self.id}" if self.id is not None else f"CPF {self.cpf}"


class FuncionarioNovo(BaseModel):
    model_config = ENTRADA
    cpf: str
    pnome: Nome
    unome: Nome
    salario: Salario
    departamento_id: Id
    minicial: Annotated[str | None, Field(max_length=1)] = None
    endereco: Annotated[str | None, Field(max_length=60)] = None
    datanasc: date | None = None
    sexo: Literal["M", "F"] | None = None
    supervisor: FuncionarioRef | None = None

    @field_validator("cpf")
    @classmethod
    def cpf_valido(cls, v: str) -> str:
        # cadastro de pessoa nova: confere os dígitos verificadores
        return validar_cpf(v)


class FuncionarioAlteracao(BaseModel):
    """Atualização parcial: model_fields_set diz o que foi informado.

    supervisor=None informado explicitamente remove o supervisor.
    """

    model_config = ENTRADA
    endereco: Annotated[str | None, Field(max_length=60)] = None
    salario: Salario | None = None
    departamento_id: Id | None = None
    supervisor: FuncionarioRef | None = None


class DepartamentoNovo(BaseModel):
    model_config = ENTRADA
    dnome: NomeLongo


class DepartamentoAlteracao(BaseModel):
    model_config = ENTRADA
    dnome: NomeLongo


class ProjetoNovo(BaseModel):
    model_config = ENTRADA
    projnome: NomeLongo
    departamento_id: Id
    projlocal: Annotated[str | None, Field(max_length=30)] = None


class ProjetoAlteracao(BaseModel):
    model_config = ENTRADA
    projnome: NomeLongo | None = None
    projlocal: Annotated[str | None, Field(max_length=30)] = None
    departamento_id: Id | None = None


class AlocacaoNova(BaseModel):
    model_config = ENTRADA
    funcionario: FuncionarioRef
    projeto_id: Id
    horas: Horas


# ------------------------------------------------------------------ saída
@dataclass(frozen=True, slots=True)
class Funcionario:
    id: int
    cpf: str
    pnome: str
    minicial: str | None
    unome: str
    datanasc: date | None
    endereco: str | None
    sexo: str | None
    salario: Decimal
    supervisor_id: int | None
    departamento_id: int | None

    @property
    def nome(self) -> str:
        partes = (self.pnome, self.minicial, self.unome)
        return " ".join(p for p in partes if p)


@dataclass(frozen=True, slots=True)
class FuncionarioResumo:
    id: int
    cpf: str
    nome: str
    departamento_id: int
    dnome: str
    salario: Decimal


@dataclass(frozen=True, slots=True)
class Departamento:
    id: int
    dnome: str
    gerente_id: int | None
    data_inicio_gerente: date | None


@dataclass(frozen=True, slots=True)
class Projeto:
    id: int
    projnome: str
    projlocal: str | None
    departamento_id: int


@dataclass(frozen=True, slots=True)
class AlocacaoDetalhe:
    funcionario_id: int
    cpf: str
    nome: str
    projeto_id: int
    projnome: str
    horas: Decimal


@dataclass(frozen=True, slots=True)
class Rejeicao:
    funcionario: str
    motivo: str


@dataclass(frozen=True, slots=True)
class ResultadoEquipe:
    alocados: list[str]
    rejeitados: list[Rejeicao]


# ------------------------------------------------------------------ relatórios
@dataclass(frozen=True, slots=True)
class ResumoDepartamento:
    id: int
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
class EquipeProjeto:
    id: int
    projnome: str
    dnome: str
    qtd_func: int
    total_horas: Decimal


@dataclass(frozen=True, slots=True)
class DependentesFuncionario:
    id: int
    cpf: str
    nome: str
    qtd_dependentes: int


@dataclass(frozen=True, slots=True)
class FuncionarioDepartamento:
    id: int
    cpf: str
    nome: str
    dnome: str
