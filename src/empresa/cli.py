"""Interface de linha de comando (argparse).

Cada subcomando converte argumentos em modelo, chama o serviço e devolve o
resultado; a impressão fica centralizada em exibir().

Códigos de saída: 0 sucesso, 1 erro de validação ou de domínio,
2 uso incorreto (argparse), 3 banco de dados indisponível.
"""

import argparse
import csv
import json
import logging
import sys
from dataclasses import asdict, fields, is_dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
from psycopg_pool import PoolTimeout
from pydantic import ValidationError

from empresa.db import criar_pool
from empresa.dto import (
    AlocacaoNova,
    DepartamentoAlteracao,
    DepartamentoNovo,
    FuncionarioAlteracao,
    FuncionarioNovo,
    ProjetoAlteracao,
    ProjetoNovo,
    ResultadoEquipe,
)
from empresa.erros import ErroDominio
from empresa.mensagens import mensagens
from empresa.servicos import Servicos
from empresa.validacao import normalizar_decimal


# ------------------------------------------------------------------ formatação
def formatar(v) -> str:
    if v is None:
        return ""
    if isinstance(v, Decimal):
        # 30000.00 -> 30.000,00 (formato brasileiro, preservando as casas)
        return f"{v:,f}".replace(",", "_").replace(".", ",").replace("_", ".")
    if isinstance(v, date):
        return v.strftime("%d/%m/%Y")
    return str(v)


def tabela(linhas: list) -> str:
    if not linhas:
        return "(nenhum registro)"
    nomes = [f.name for f in fields(linhas[0])]
    dados = [[formatar(getattr(x, n)) for n in nomes] for x in linhas]
    larg = [max(len(n), *(len(d[i]) for d in dados)) for i, n in enumerate(nomes)]
    fmt = "  ".join(f"{{:<{w}}}" for w in larg)
    return "\n".join(
        [fmt.format(*nomes), fmt.format(*("-" * w for w in larg))] + [fmt.format(*d) for d in dados]
    )


def arvore(no: dict, prefixo: str = "", raiz: bool = True) -> list[str]:
    linhas = [f"{no['nome']} ({no['cpf']})"] if raiz else []
    equipe = no["equipe"]
    for i, filho in enumerate(equipe):
        ultimo = i == len(equipe) - 1
        linhas.append(
            prefixo + ("└── " if ultimo else "├── ") + f"{filho['nome']} ({filho['cpf']})"
        )
        linhas += arvore(filho, prefixo + ("    " if ultimo else "│   "), raiz=False)
    return linhas


def exibir(res, como_json: bool) -> None:
    if res is None:
        return
    if como_json:
        obj = (
            [asdict(x) for x in res]
            if isinstance(res, list)
            else (asdict(res) if is_dataclass(res) else res)
        )
        print(json.dumps(obj, default=str, ensure_ascii=False, indent=2))
    elif isinstance(res, str):
        print(res)
    elif isinstance(res, ResultadoEquipe):
        print("Alocados:", ", ".join(res.alocados) or "nenhum")
        for r in res.rejeitados:
            print(f"Rejeitado {r.cpf}: {r.motivo}")
    elif isinstance(res, list):
        print(tabela(res))
    elif isinstance(res, dict):
        print("\n".join(arvore(res)))
    elif is_dataclass(res):
        for f in fields(res):
            print(f"{f.name:<20} {formatar(getattr(res, f.name))}")


def informados(a: argparse.Namespace, mapa: dict[str, str]) -> dict:
    """Só os argumentos informados, para que exclude_unset funcione."""
    return {campo: getattr(a, arg) for arg, campo in mapa.items() if getattr(a, arg) is not None}


# ------------------------------------------------------------------ comandos
def func_criar(s: Servicos, a):
    novo = FuncionarioNovo(
        cpf=a.cpf,
        pnome=a.pnome,
        minicial=a.minicial,
        unome=a.unome,
        salario=normalizar_decimal(a.salario),
        dnr=a.dep,
        datanasc=a.datanasc,
        endereco=a.endereco,
        sexo=a.sexo,
        cpf_supervisor=a.supervisor,
    )
    return s.funcionarios.criar(novo)


def func_atualizar(s: Servicos, a):
    if a.salario is not None:
        a.salario = normalizar_decimal(a.salario)
    campos = informados(
        a,
        {
            "endereco": "endereco",
            "salario": "salario",
            "dep": "dnr",
            "supervisor": "cpf_supervisor",
        },
    )
    return s.funcionarios.atualizar(a.cpf, FuncionarioAlteracao(**campos))


def func_listar(s: Servicos, a):
    smin = Decimal(normalizar_decimal(a.salario_min)) if a.salario_min else None
    return s.funcionarios.listar(
        dnr=a.dep, nome=a.nome, salario_min=smin, limite=a.limite, pagina=a.pagina
    )


def func_remover(s: Servicos, a):
    s.funcionarios.remover(a.cpf)
    return f"Funcionário {a.cpf} removido."


def dep_remover(s: Servicos, a):
    s.departamentos.remover(a.numero)
    return f"Departamento {a.numero} removido."


def proj_atualizar(s: Servicos, a):
    campos = informados(a, {"nome": "projnome", "local": "projlocal", "dep": "dnum"})
    return s.projetos.atualizar(a.numero, ProjetoAlteracao(**campos))


def proj_remover(s: Servicos, a):
    s.projetos.remover(a.numero)
    return f"Projeto {a.numero} removido."


def aloc_criar(s: Servicos, a):
    s.alocacoes.alocar(
        AlocacaoNova(cpf=a.cpf, projnumero=a.projeto, horas=normalizar_decimal(a.horas))
    )
    return f"Funcionário {a.cpf} alocado no projeto {a.projeto}."


def aloc_equipe(s: Servicos, a):
    # arquivo CSV com cpf;horas por linha
    with open(a.arquivo, newline="", encoding="utf-8") as arq:
        equipe = [
            AlocacaoNova(cpf=cpf, projnumero=a.projeto, horas=normalizar_decimal(horas))
            for cpf, horas in csv.reader(arq, delimiter=";")
            if cpf.strip()
        ]
    return s.alocacoes.alocar_equipe(a.projeto, equipe)


def aloc_remover(s: Servicos, a):
    s.alocacoes.remover(a.cpf, a.projeto)
    return f"Alocação de {a.cpf} no projeto {a.projeto} removida."


def rel_exportar(s: Servicos, a):
    n = s.relatorios.exportar_csv(Path(a.arquivo))
    return f"{n} funcionários exportados para {a.arquivo}."


# ------------------------------------------------------------------ parser
def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="empresa", description="Gestão do esquema EMPRESA")
    p.add_argument("--json", action="store_true", help="saída em JSON")
    rec = p.add_subparsers(dest="recurso", required=True, metavar="RECURSO")

    def acoes(nome: str, ajuda: str):
        sp = rec.add_parser(nome, help=ajuda)
        return sp.add_subparsers(dest="acao", required=True, metavar="AÇÃO")

    def cmd(grupo, nome: str, ajuda: str, func):
        c = grupo.add_parser(nome, help=ajuda)
        c.set_defaults(func=func)
        return c

    # funcionario
    g = acoes("funcionario", "CRUD de funcionários")
    c = cmd(g, "criar", "cadastra funcionário", func_criar)
    for op in ("--cpf", "--pnome", "--unome", "--salario"):
        c.add_argument(op, required=True)
    c.add_argument("--dep", required=True, help="número do departamento")
    for op in ("--minicial", "--datanasc", "--endereco", "--sexo", "--supervisor"):
        c.add_argument(op)
    c = cmd(g, "obter", "mostra um funcionário", lambda s, a: s.funcionarios.obter(a.cpf))
    c.add_argument("cpf")
    c = cmd(g, "listar", "lista com filtros e paginação", func_listar)
    c.add_argument("--dep", type=int)
    c.add_argument("--nome")
    c.add_argument("--salario-min")
    c.add_argument("--limite", type=int, default=20)
    c.add_argument("--pagina", type=int, default=1)
    c = cmd(g, "atualizar", "altera campos informados", func_atualizar)
    c.add_argument("cpf")
    for op in ("--endereco", "--salario", "--dep", "--supervisor"):
        c.add_argument(op)
    c = cmd(g, "remover", "exclui funcionário", func_remover)
    c.add_argument("cpf")

    # departamento
    g = acoes("departamento", "CRUD de departamentos")
    c = cmd(
        g,
        "criar",
        "cadastra departamento",
        lambda s, a: s.departamentos.criar(DepartamentoNovo(dnumero=a.numero, dnome=a.nome)),
    )
    c.add_argument("--numero", required=True)
    c.add_argument("--nome", required=True)
    c = cmd(g, "obter", "mostra um departamento", lambda s, a: s.departamentos.obter(a.numero))
    c.add_argument("numero", type=int)
    cmd(g, "listar", "lista departamentos", lambda s, a: s.departamentos.listar())
    c = cmd(
        g,
        "renomear",
        "altera o nome",
        lambda s, a: s.departamentos.renomear(a.numero, DepartamentoAlteracao(dnome=a.nome)),
    )
    c.add_argument("numero", type=int)
    c.add_argument("--nome", required=True)
    c = cmd(g, "remover", "exclui departamento", dep_remover)
    c.add_argument("numero", type=int)
    c = cmd(
        g,
        "trocar-gerente",
        "define o gerente (transação com vários comandos)",
        lambda s, a: s.departamentos.trocar_gerente(a.numero, a.cpf),
    )
    c.add_argument("numero", type=int)
    c.add_argument("--cpf", required=True)

    # projeto
    g = acoes("projeto", "CRUD de projetos")
    c = cmd(
        g,
        "criar",
        "cadastra projeto (número gerado pelo banco)",
        lambda s, a: s.projetos.criar(ProjetoNovo(projnome=a.nome, projlocal=a.local, dnum=a.dep)),
    )
    c.add_argument("--nome", required=True)
    c.add_argument("--local")
    c.add_argument("--dep", required=True)
    c = cmd(g, "obter", "mostra um projeto", lambda s, a: s.projetos.obter(a.numero))
    c.add_argument("numero", type=int)
    c = cmd(g, "listar", "lista projetos", lambda s, a: s.projetos.listar(a.dep))
    c.add_argument("--dep", type=int)
    c = cmd(g, "atualizar", "altera campos informados", proj_atualizar)
    c.add_argument("numero", type=int)
    for op in ("--nome", "--local", "--dep"):
        c.add_argument(op)
    c = cmd(g, "remover", "exclui projeto", proj_remover)
    c.add_argument("numero", type=int)

    # alocação
    g = acoes("alocacao", "alocação de funcionários em projetos")
    c = cmd(g, "criar", "aloca respeitando o limite de 40 h semanais", aloc_criar)
    c.add_argument("--cpf", required=True)
    c.add_argument("--projeto", type=int, required=True)
    c.add_argument("--horas", required=True)
    c = cmd(g, "equipe", "aloca uma equipe a partir de CSV cpf;horas (savepoints)", aloc_equipe)
    c.add_argument("--projeto", type=int, required=True)
    c.add_argument("--arquivo", required=True)
    c = cmd(g, "listar", "alocações de um projeto", lambda s, a: s.alocacoes.por_projeto(a.projeto))
    c.add_argument("--projeto", type=int, required=True)
    c = cmd(g, "remover", "remove uma alocação", aloc_remover)
    c.add_argument("--cpf", required=True)
    c.add_argument("--projeto", type=int, required=True)

    # relatórios
    g = acoes("relatorio", "consultas de negócio")
    cmd(
        g,
        "departamentos",
        "folha, média e projetos por departamento (visão)",
        lambda s, a: s.relatorios.departamentos(),
    )
    c = cmd(
        g, "ranking", "ranking salarial por departamento", lambda s, a: s.relatorios.ranking(a.dep)
    )
    c.add_argument("--dep", type=int, nargs="*", help="departamentos (padrão: todos)")
    cmd(
        g,
        "todos-projetos",
        "alocados em todos os projetos do próprio departamento",
        lambda s, a: s.relatorios.todos_projetos(),
    )
    c = cmd(
        g,
        "supervisao",
        "cadeia de supervisão (consulta recursiva)",
        lambda s, a: s.relatorios.supervisao(a.cpf),
    )
    c.add_argument("cpf")
    c = cmd(g, "exportar", "exporta funcionários em CSV (cursor nomeado)", rel_exportar)
    c.add_argument("arquivo")
    return p


def main(argv: list[str] | None = None) -> None:
    a = construir_parser().parse_args(argv)
    # na CLI, as tentativas de reconexão do pool não precisam aparecer no terminal
    logging.getLogger("psycopg.pool").setLevel(logging.CRITICAL)
    try:
        servicos = Servicos(criar_pool(min_size=1, espera=5))
        exibir(a.func(servicos, a), a.json)
    except ValidationError as e:
        sys.exit("\n".join(["Dados inválidos:"] + mensagens(e.errors())))
    except ErroDominio as e:
        sys.exit("Erro: " + str(e))
    except (PoolTimeout, psycopg.OperationalError) as e:
        print("Erro: banco de dados indisponível:", e, file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
