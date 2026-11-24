"""Interface web (FastAPI), opcional, sobre os mesmos serviços da CLI.

Execução em desenvolvimento:

    uv run --env-file .env fastapi dev src/empresa/api.py

As rotas são `def` síncronas: o FastAPI as executa em threads e o Psycopg
síncrono funciona sem mudança. Documentação interativa em /docs.
"""

from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from empresa.db import criar_pool
from empresa.dto import (
    AlocacaoDetalhe,
    AlocacaoNova,
    Departamento,
    DepartamentoAlteracao,
    DepartamentoNovo,
    Funcionario,
    FuncionarioAlteracao,
    FuncionarioDepartamento,
    FuncionarioNovo,
    FuncionarioResumo,
    GerenteNovo,
    PosicaoSalarial,
    Projeto,
    ProjetoAlteracao,
    ProjetoNovo,
    ResumoDepartamento,
)
from empresa.erros import (
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


@app.exception_handler(RequestValidationError)
def erro_validacao(request: Request, e: RequestValidationError):
    erros = mensagens(e.errors())
    return JSONResponse({"erros": erros}, status_code=422)


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
        dnr=dep, nome=nome, salario_min=salario_min, limite=limite, pagina=pagina
    )


@app.get("/funcionarios/{cpf}")
def obter_funcionario(cpf: str, s: S) -> Funcionario:
    return s.funcionarios.obter(cpf)


@app.patch("/funcionarios/{cpf}")
def atualizar_funcionario(cpf: str, alteracao: FuncionarioAlteracao, s: S) -> Funcionario:
    return s.funcionarios.atualizar(cpf, alteracao)


@app.delete("/funcionarios/{cpf}", status_code=204)
def remover_funcionario(cpf: str, s: S) -> None:
    s.funcionarios.remover(cpf)


# ------------------------------------------------------------------ departamentos
@app.post("/departamentos", status_code=201)
def criar_departamento(novo: DepartamentoNovo, s: S) -> Departamento:
    return s.departamentos.criar(novo)


@app.get("/departamentos")
def listar_departamentos(s: S) -> list[Departamento]:
    return s.departamentos.listar()


@app.get("/departamentos/{dnumero}")
def obter_departamento(dnumero: int, s: S) -> Departamento:
    return s.departamentos.obter(dnumero)


@app.patch("/departamentos/{dnumero}")
def renomear_departamento(dnumero: int, alteracao: DepartamentoAlteracao, s: S) -> Departamento:
    return s.departamentos.renomear(dnumero, alteracao)


@app.put("/departamentos/{dnumero}/gerente")
def trocar_gerente(dnumero: int, gerente: GerenteNovo, s: S) -> Departamento:
    return s.departamentos.trocar_gerente(dnumero, gerente.cpf)


@app.delete("/departamentos/{dnumero}", status_code=204)
def remover_departamento(dnumero: int, s: S) -> None:
    s.departamentos.remover(dnumero)


# ------------------------------------------------------------------ projetos
@app.post("/projetos", status_code=201)
def criar_projeto(novo: ProjetoNovo, s: S) -> Projeto:
    return s.projetos.criar(novo)


@app.get("/projetos")
def listar_projetos(s: S, dep: int | None = None) -> list[Projeto]:
    return s.projetos.listar(dep)


@app.get("/projetos/{projnumero}")
def obter_projeto(projnumero: int, s: S) -> Projeto:
    return s.projetos.obter(projnumero)


@app.patch("/projetos/{projnumero}")
def atualizar_projeto(projnumero: int, alteracao: ProjetoAlteracao, s: S) -> Projeto:
    return s.projetos.atualizar(projnumero, alteracao)


@app.delete("/projetos/{projnumero}", status_code=204)
def remover_projeto(projnumero: int, s: S) -> None:
    s.projetos.remover(projnumero)


@app.get("/projetos/{projnumero}/alocacoes")
def listar_alocacoes(projnumero: int, s: S) -> list[AlocacaoDetalhe]:
    return s.alocacoes.por_projeto(projnumero)


# ------------------------------------------------------------------ alocações
@app.post("/alocacoes", status_code=201)
def alocar(nova: AlocacaoNova, s: S) -> AlocacaoNova:
    s.alocacoes.alocar(nova)
    return nova


@app.delete("/alocacoes/{cpf}/{projnumero}", status_code=204)
def remover_alocacao(cpf: str, projnumero: int, s: S) -> None:
    s.alocacoes.remover(cpf, projnumero)


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


@app.get("/relatorios/supervisao/{cpf}")
def relatorio_supervisao(cpf: str, s: S) -> dict:
    return s.relatorios.supervisao(cpf)
