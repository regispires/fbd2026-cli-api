from decimal import Decimal

import pytest

from empresa.dto import (
    AlocacaoNova,
    DepartamentoNovo,
    FuncionarioAlteracao,
    FuncionarioNovo,
    ProjetoNovo,
)
from empresa.erros import Duplicidade, NaoEncontrado, ReferenciaInvalida, RegraViolada

ANA = FuncionarioNovo(cpf="52998224725", pnome="Ana", unome="Lima", salario="4200", dnr=5)


# ------------------------------------------------------------------ CRUD
def test_criar_e_obter_funcionario(servicos):
    criado = servicos.funcionarios.criar(ANA)
    assert servicos.funcionarios.obter("52998224725") == criado


def test_cpf_duplicado_vira_duplicidade(servicos):
    servicos.funcionarios.criar(ANA)
    with pytest.raises(Duplicidade, match="Já existe funcionário com este CPF"):
        servicos.funcionarios.criar(ANA)


def test_departamento_inexistente_vira_referencia_invalida(servicos):
    novo = ANA.model_copy(update={"dnr": 99})
    with pytest.raises(ReferenciaInvalida, match="Departamento informado não existe"):
        servicos.funcionarios.criar(novo)


def test_obter_inexistente(servicos):
    with pytest.raises(NaoEncontrado):
        servicos.funcionarios.obter("00000000000")


def test_atualizacao_parcial(servicos):
    f = servicos.funcionarios.atualizar("12345678966", FuncionarioAlteracao(salario="32000"))
    assert f.salario == Decimal("32000.00")
    assert f.endereco == "Rua das Flores, 751, São Paulo, SP"


def test_remover_gerente_e_bloqueado(servicos):
    with pytest.raises(ReferenciaInvalida, match="departamento"):
        servicos.funcionarios.remover("33344555587")


def test_criar_projeto_devolve_numero_gerado(servicos):
    p = servicos.projetos.criar(ProjetoNovo(projnome="ProdutoW", dnum=5))
    assert p.projnumero == 31


def test_remover_departamento_com_funcionarios(servicos):
    with pytest.raises(ReferenciaInvalida):
        servicos.departamentos.remover(5)


def test_criar_e_remover_departamento(servicos):
    servicos.departamentos.criar(DepartamentoNovo(dnumero=6, dnome="Logística"))
    servicos.departamentos.remover(6)
    with pytest.raises(NaoEncontrado):
        servicos.departamentos.obter(6)


# ------------------------------------------------------------------ transações
def test_alocacao_acima_de_40_horas_e_revertida(servicos):
    with pytest.raises(RegraViolada):
        servicos.alocacoes.alocar(AlocacaoNova(cpf="12345678966", projnumero=3, horas="1"))
    cpfs = [a.cpf for a in servicos.alocacoes.por_projeto(3)]
    assert "12345678966" not in cpfs


def test_alocacao_dentro_do_limite(servicos):
    servicos.alocacoes.alocar(AlocacaoNova(cpf="98765432168", projnumero=10, horas="5"))
    assert "98765432168" in [a.cpf for a in servicos.alocacoes.por_projeto(10)]


def test_alocar_equipe_com_savepoints(servicos):
    servicos.funcionarios.criar(ANA)
    equipe = [
        AlocacaoNova(cpf="52998224725", projnumero=1, horas="8"),
        AlocacaoNova(cpf="12345678966", projnumero=3, horas="1"),  # passa de 40 h
        AlocacaoNova(cpf="99999999999", projnumero=1, horas="1"),  # inexistente
    ]
    res = servicos.alocacoes.alocar_equipe(1, equipe)
    assert res.alocados == ["52998224725"]
    assert [r.cpf for r in res.rejeitados] == ["12345678966", "99999999999"]
    assert "52998224725" in [a.cpf for a in servicos.alocacoes.por_projeto(1)]


def test_trocar_gerente_altera_as_duas_tabelas(servicos):
    servicos.funcionarios.criar(ANA)
    dep = servicos.departamentos.trocar_gerente(4, "52998224725")
    assert dep.cpf_gerente == "52998224725"
    assert servicos.funcionarios.obter("52998224725").dnr == 4


def test_trocar_gerente_inexistente_nao_altera_nada(servicos):
    with pytest.raises(NaoEncontrado):
        servicos.departamentos.trocar_gerente(99, "12345678966")
    assert servicos.funcionarios.obter("12345678966").dnr == 5


# ------------------------------------------------------------------ relatórios
def test_relatorio_departamentos(servicos):
    rel = {r.dnome: r for r in servicos.relatorios.departamentos()}
    assert rel["Pesquisa"].qtd_func == 4
    assert rel["Pesquisa"].folha == Decimal("133000.00")


def test_ranking_salarial(servicos):
    rk = servicos.relatorios.ranking([4])
    assert [(r.nome, r.posicao) for r in rk] == [
        ("Jennifer S Souza", 1),
        ("Alice J Zelaya", 2),
        ("André V Pereira", 2),
    ]


def test_divisao_relacional(servicos):
    nomes = [r.nome for r in servicos.relatorios.todos_projetos()]
    assert nomes == ["Alice J Zelaya", "André V Pereira"]


def test_cadeia_de_supervisao(servicos):
    arv = servicos.relatorios.supervisao("88866555576")
    assert arv["nome"] == "Jorge Brito"
    assert sorted(f["nome"] for f in arv["equipe"]) == ["Fernando Wong", "Jennifer Souza"]


def test_exportar_csv(servicos, tmp_path):
    destino = tmp_path / "func.csv"
    assert servicos.relatorios.exportar_csv(destino) == 8
    assert destino.read_text(encoding="utf-8").startswith("cpf;nome;dnome;salario")
