"""Interface web (FastAPI) sobre os mesmos serviços da CLI.

Execução em desenvolvimento:

    uv run fastapi dev src/empresa/api.py

As rotas são `def` síncronas: o FastAPI as executa em threads e o Psycopg
síncrono funciona sem mudança. Documentação interativa em /docs.

Um funcionário pode ser acessado pelo id (/funcionarios/{id}) ou pelo CPF
(/funcionarios/cpf/{cpf}); nos corpos JSON, por {"id": ...} ou {"cpf": ...}.
"""

from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from empresa.db import criar_pool
from empresa.dto import (
    AlocacaoDetalhe,
    AlocacaoNova,
    Departamento,
    DepartamentoAlteracao,
    DepartamentoNovo,
    DependentesFuncionario,
    EquipeProjeto,
    Funcionario,
    FuncionarioAlteracao,
    FuncionarioDepartamento,
    FuncionarioNovo,
    FuncionarioRef,
    FuncionarioResumo,
    PosicaoSalarial,
    Projeto,
    ProjetoAlteracao,
    ProjetoNovo,
    ResumoDepartamento,
)
from empresa.erros import (
    ESQUEMA_AUSENTE,
    DadosInvalidos,
    Duplicidade,
    ErroDominio,
    NaoEncontrado,
    ReferenciaInvalida,
    RegraViolada,
)
from empresa.mensagens import mensagens
from empresa.servicos import Servicos


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = criar_pool()  # um pool por processo
    app.state.servicos = Servicos(pool)
    yield
    pool.close()


app = FastAPI(title="EMPRESA", lifespan=lifespan)


def servicos(request: Request) -> Servicos:
    return request.app.state.servicos


S = Annotated[Servicos, Depends(servicos)]


def por_cpf(cpf: str) -> FuncionarioRef:
    return FuncionarioRef(cpf=cpf)


def por_id(id: int) -> FuncionarioRef:
    return FuncionarioRef(id=id)


# ------------------------------------------------------------------ erros
STATUS = {
    NaoEncontrado: 404,
    Duplicidade: 409,
    ReferenciaInvalida: 409,
    DadosInvalidos: 422,
    RegraViolada: 422,
}


@app.exception_handler(ErroDominio)
def erro_dominio(request: Request, e: ErroDominio):
    status = STATUS.get(type(e), 400)
    return JSONResponse({"erros": [str(e)]}, status_code=status)


@app.exception_handler(psycopg.errors.UndefinedTable)
def esquema_ausente(request: Request, e: psycopg.errors.UndefinedTable):
    # a API subiu antes de `empresa banco criar`
    return JSONResponse({"erros": [ESQUEMA_AUSENTE]}, status_code=503)


@app.exception_handler(RequestValidationError)
def erro_validacao(request: Request, e: RequestValidationError):
    erros = mensagens(e.errors())
    return JSONResponse({"erros": erros}, status_code=422)


@app.exception_handler(ValidationError)
def erro_modelo(request: Request, e: ValidationError):
    # modelo montado dentro da rota, como FuncionarioRef(cpf=...) a partir da URL
    return JSONResponse({"erros": mensagens(e.errors())}, status_code=422)


# ------------------------------------------------------------------ funcionários
@app.post("/funcionarios", status_code=201)
def criar_funcionario(novo: FuncionarioNovo, s: S) -> Funcionario:
    return s.funcionarios.criar(novo)


@app.get("/funcionarios")
def listar_funcionarios(
    s: S,
    dep: int | None = None,
    nome: str | None = None,
    salario_min: Decimal | None = None,
    limite: Annotated[int, Query(ge=1, le=100)] = 20,
    pagina: Annotated[int, Query(ge=1)] = 1,
) -> list[FuncionarioResumo]:
    return s.funcionarios.listar(
        departamento_id=dep, nome=nome, salario_min=salario_min, limite=limite, pagina=pagina
    )


@app.get("/funcionarios/{id}")
def obter_funcionario(id: int, s: S) -> Funcionario:
    return s.funcionarios.obter(por_id(id))


@app.get("/funcionarios/cpf/{cpf}")
def obter_funcionario_por_cpf(cpf: str, s: S) -> Funcionario:
    return s.funcionarios.obter(por_cpf(cpf))


@app.patch("/funcionarios/{id}")
def atualizar_funcionario(id: int, alteracao: FuncionarioAlteracao, s: S) -> Funcionario:
    return s.funcionarios.atualizar(por_id(id), alteracao)


@app.patch("/funcionarios/cpf/{cpf}")
def atualizar_funcionario_por_cpf(cpf: str, alteracao: FuncionarioAlteracao, s: S) -> Funcionario:
    return s.funcionarios.atualizar(por_cpf(cpf), alteracao)


@app.delete("/funcionarios/{id}", status_code=204)
def remover_funcionario(id: int, s: S) -> None:
    s.funcionarios.remover(por_id(id))


@app.delete("/funcionarios/cpf/{cpf}", status_code=204)
def remover_funcionario_por_cpf(cpf: str, s: S) -> None:
    s.funcionarios.remover(por_cpf(cpf))


# ------------------------------------------------------------------ departamentos
@app.post("/departamentos", status_code=201)
def criar_departamento(novo: DepartamentoNovo, s: S) -> Departamento:
    return s.departamentos.criar(novo)


@app.get("/departamentos")
def listar_departamentos(s: S) -> list[Departamento]:
    return s.departamentos.listar()


@app.get("/departamentos/{id}")
def obter_departamento(id: int, s: S) -> Departamento:
    return s.departamentos.obter(id)


@app.patch("/departamentos/{id}")
def renomear_departamento(id: int, alteracao: DepartamentoAlteracao, s: S) -> Departamento:
    return s.departamentos.renomear(id, alteracao)


@app.put("/departamentos/{id}/gerente")
def trocar_gerente(id: int, gerente: FuncionarioRef, s: S) -> Departamento:
    return s.departamentos.trocar_gerente(id, gerente)


@app.delete("/departamentos/{id}", status_code=204)
def remover_departamento(id: int, s: S) -> None:
    s.departamentos.remover(id)


# ------------------------------------------------------------------ projetos
@app.post("/projetos", status_code=201)
def criar_projeto(novo: ProjetoNovo, s: S) -> Projeto:
    return s.projetos.criar(novo)


@app.get("/projetos")
def listar_projetos(s: S, dep: int | None = None) -> list[Projeto]:
    return s.projetos.listar(dep)


@app.get("/projetos/{id}")
def obter_projeto(id: int, s: S) -> Projeto:
    return s.projetos.obter(id)


@app.patch("/projetos/{id}")
def atualizar_projeto(id: int, alteracao: ProjetoAlteracao, s: S) -> Projeto:
    return s.projetos.atualizar(id, alteracao)


@app.delete("/projetos/{id}", status_code=204)
def remover_projeto(id: int, s: S) -> None:
    s.projetos.remover(id)


@app.get("/projetos/{id}/alocacoes")
def listar_alocacoes(id: int, s: S) -> list[AlocacaoDetalhe]:
    return s.alocacoes.por_projeto(id)


# ------------------------------------------------------------------ alocações
@app.post("/alocacoes", status_code=201)
def alocar(nova: AlocacaoNova, s: S) -> AlocacaoNova:
    s.alocacoes.alocar(nova)
    return nova


@app.delete("/alocacoes/{funcionario_id}/{projeto_id}", status_code=204)
def remover_alocacao(funcionario_id: int, projeto_id: int, s: S) -> None:
    s.alocacoes.remover(por_id(funcionario_id), projeto_id)


@app.delete("/alocacoes/cpf/{cpf}/{projeto_id}", status_code=204)
def remover_alocacao_por_cpf(cpf: str, projeto_id: int, s: S) -> None:
    s.alocacoes.remover(por_cpf(cpf), projeto_id)


# ------------------------------------------------------------------ relatórios
@app.get("/relatorios/departamentos")
def relatorio_departamentos(s: S) -> list[ResumoDepartamento]:
    return s.relatorios.departamentos()


@app.get("/relatorios/ranking")
def relatorio_ranking(
    s: S, dep: Annotated[list[int] | None, Query()] = None
) -> list[PosicaoSalarial]:
    return s.relatorios.ranking(dep)


@app.get("/relatorios/todos-projetos")
def relatorio_todos_projetos(s: S) -> list[FuncionarioDepartamento]:
    return s.relatorios.todos_projetos()


@app.get("/relatorios/equipes")
def relatorio_equipes(s: S, max_func: Annotated[int, Query(ge=0)]) -> list[EquipeProjeto]:
    return s.relatorios.equipes(max_func)


@app.get("/relatorios/dependentes")
def relatorio_dependentes(
    s: S, min: Annotated[int, Query(ge=0)] = 0
) -> list[DependentesFuncionario]:
    return s.relatorios.dependentes(min)


@app.get("/relatorios/supervisao/{id}")
def relatorio_supervisao(id: int, s: S) -> dict:
    return s.relatorios.supervisao(por_id(id))


@app.get("/relatorios/supervisao/cpf/{cpf}")
def relatorio_supervisao_por_cpf(cpf: str, s: S) -> dict:
    return s.relatorios.supervisao(por_cpf(cpf))
