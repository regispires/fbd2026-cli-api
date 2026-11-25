from decimal import Decimal

import pytest

from empresa.dto import (
    AlocacaoNova,
    DepartamentoNovo,
    FuncionarioAlteracao,
    FuncionarioNovo,
    FuncionarioRef,
    ProjetoNovo,
)
from empresa.erros import (
    DadosInvalidos,
    Duplicidade,
    NaoEncontrado,
    ReferenciaInvalida,
    RegraViolada,
)

ANA = FuncionarioNovo(
    cpf="52998224725", pnome="Ana", unome="Lima", salario="4200", departamento_id=5
)
JOAO_CPF = FuncionarioRef(cpf="12345678966")
JOAO_ID = FuncionarioRef(id=1)


# ------------------------------------------------------------------ CRUD
def test_criar_devolve_id_gerado_e_obter_pelos_dois_caminhos(servicos):
    criado = servicos.funcionarios.criar(ANA)
    assert criado.id == 9
    assert servicos.funcionarios.obter(FuncionarioRef(id=9)) == criado
    assert servicos.funcionarios.obter(FuncionarioRef(cpf="529.982.247-25")) == criado


def test_supervisor_indicado_por_cpf_vira_id(servicos):
    novo = ANA.model_copy(update={"supervisor": FuncionarioRef(cpf="33344555587")})
    assert servicos.funcionarios.criar(novo).supervisor_id == 2


def test_supervisor_inexistente(servicos):
    novo = ANA.model_copy(update={"supervisor": FuncionarioRef(id=999)})
    with pytest.raises(NaoEncontrado, match="id 999"):
        servicos.funcionarios.criar(novo)


def test_cpf_duplicado_vira_duplicidade(servicos):
    servicos.funcionarios.criar(ANA)
    with pytest.raises(Duplicidade, match="Já existe funcionário com este CPF"):
        servicos.funcionarios.criar(ANA)


def test_departamento_inexistente_vira_referencia_invalida(servicos):
    novo = ANA.model_copy(update={"departamento_id": 99})
    with pytest.raises(ReferenciaInvalida, match="Departamento informado não existe"):
        servicos.funcionarios.criar(novo)


def test_obter_inexistente(servicos):
    with pytest.raises(NaoEncontrado):
        servicos.funcionarios.obter(FuncionarioRef(cpf="00000000000"))


@pytest.mark.parametrize("ref", [JOAO_ID, JOAO_CPF])
def test_atualizacao_parcial_por_id_ou_cpf(servicos, ref):
    f = servicos.funcionarios.atualizar(ref, FuncionarioAlteracao(salario="32000"))
    assert f.salario == Decimal("32000.00")
    assert f.endereco == "Rua das Flores, 751, São Paulo, SP"


def test_atualizacao_remove_supervisor(servicos):
    f = servicos.funcionarios.atualizar(JOAO_ID, FuncionarioAlteracao(supervisor=None))
    assert f.supervisor_id is None


def test_remover_gerente_e_bloqueado(servicos):
    with pytest.raises(ReferenciaInvalida, match="departamento"):
        servicos.funcionarios.remover(FuncionarioRef(cpf="33344555587"))


def test_criar_projeto_devolve_id_gerado(servicos):
    p = servicos.projetos.criar(ProjetoNovo(projnome="ProdutoW", departamento_id=5))
    assert p.id == 41


def test_remover_departamento_com_funcionarios(servicos):
    with pytest.raises(ReferenciaInvalida):
        servicos.departamentos.remover(5)


def test_criar_e_remover_departamento(servicos):
    dep = servicos.departamentos.criar(DepartamentoNovo(dnome="Logística"))
    assert dep.id == 7
    servicos.departamentos.remover(dep.id)
    with pytest.raises(NaoEncontrado):
        servicos.departamentos.obter(dep.id)


def test_nome_de_departamento_duplicado(servicos):
    with pytest.raises(Duplicidade, match="Nome de departamento já usado"):
        servicos.departamentos.criar(DepartamentoNovo(dnome="Pesquisa"))


# ------------------------------------------------------------------ transações
def test_alocacao_acima_de_40_horas_e_revertida(servicos):
    with pytest.raises(RegraViolada):
        servicos.alocacoes.alocar(AlocacaoNova(funcionario=JOAO_CPF, projeto_id=3, horas="1"))
    assert 1 not in [a.funcionario_id for a in servicos.alocacoes.por_projeto(3)]


def test_alocacao_dentro_do_limite_por_id(servicos):
    jennifer = FuncionarioRef(id=4)
    servicos.alocacoes.alocar(AlocacaoNova(funcionario=jennifer, projeto_id=10, horas="5"))
    assert 4 in [a.funcionario_id for a in servicos.alocacoes.por_projeto(10)]


def test_alocar_equipe_com_savepoints(servicos):
    servicos.funcionarios.criar(ANA)
    equipe = [
        AlocacaoNova(funcionario=FuncionarioRef(cpf="52998224725"), projeto_id=1, horas="8"),
        AlocacaoNova(funcionario=JOAO_ID, projeto_id=1, horas="1"),  # passa de 40 h
        AlocacaoNova(funcionario=FuncionarioRef(id=999), projeto_id=1, horas="1"),  # inexistente
    ]
    res = servicos.alocacoes.alocar_equipe(1, equipe)
    assert res.alocados == ["CPF 52998224725"]
    assert [r.funcionario for r in res.rejeitados] == ["id 1", "id 999"]
    assert 9 in [a.funcionario_id for a in servicos.alocacoes.por_projeto(1)]


def test_trocar_gerente_altera_as_duas_tabelas(servicos):
    servicos.funcionarios.criar(ANA)
    dep = servicos.departamentos.trocar_gerente(4, FuncionarioRef(cpf="52998224725"))
    assert dep.gerente_id == 9
    assert servicos.funcionarios.obter(FuncionarioRef(id=9)).departamento_id == 4


def test_trocar_gerente_inexistente_nao_altera_nada(servicos):
    with pytest.raises(NaoEncontrado):
        servicos.departamentos.trocar_gerente(99, JOAO_ID)
    assert servicos.funcionarios.obter(JOAO_ID).departamento_id == 5


# ------------------------------------------------------------------ relatórios
def test_relatorio_departamentos(servicos):
    rel = {r.dnome: r for r in servicos.relatorios.departamentos()}
    assert rel["Pesquisa"].qtd_func == 4
    assert rel["Pesquisa"].folha == Decimal("133000.00")


def test_relatorio_departamentos_inclui_departamento_vazio(servicos):
    # LEFT JOIN na visão: o departamento sem funcionários aparece com zeros
    vazio = {r.dnome: r for r in servicos.relatorios.departamentos()}["Expansão"]
    assert (vazio.qtd_func, vazio.folha, vazio.media, vazio.qtd_proj) == (0, 0, None, 0)


def test_equipes_inclui_projeto_sem_alocacao(servicos):
    rel = servicos.relatorios.equipes(2)
    assert [(e.projnome, e.qtd_func) for e in rel] == [
        ("Portal do Cliente", 0),
        ("ProdutoX", 2),
        ("ProdutoZ", 2),
        ("Reorganização", 2),
    ]
    assert rel[0].total_horas == 0


def test_equipes_com_zero_mostra_so_projetos_vazios(servicos):
    assert [e.id for e in servicos.relatorios.equipes(0)] == [40]


def test_dependentes_com_minimo_zero_inclui_quem_nao_tem(servicos):
    rel = servicos.relatorios.dependentes()
    assert len(rel) == 8
    assert sum(1 for r in rel if r.qtd_dependentes == 0) == 5


def test_dependentes_com_minimo(servicos):
    rel = servicos.relatorios.dependentes(2)
    assert [(r.nome, r.qtd_dependentes) for r in rel] == [
        ("Fernando T Wong", 3),
        ("João B Silva", 3),
    ]


def test_limite_negativo_e_rejeitado(servicos):
    with pytest.raises(DadosInvalidos):
        servicos.relatorios.equipes(-1)


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


@pytest.mark.parametrize("raiz", [FuncionarioRef(id=8), FuncionarioRef(cpf="88866555576")])
def test_cadeia_de_supervisao(servicos, raiz):
    arv = servicos.relatorios.supervisao(raiz)
    assert (arv["id"], arv["nome"]) == (8, "Jorge Brito")
    assert sorted(f["nome"] for f in arv["equipe"]) == ["Fernando Wong", "Jennifer Souza"]


def test_exportar_csv(servicos, tmp_path):
    destino = tmp_path / "func.csv"
    assert servicos.relatorios.exportar_csv(destino) == 8
    assert destino.read_text(encoding="utf-8").startswith("id;cpf;nome;dnome;salario")
