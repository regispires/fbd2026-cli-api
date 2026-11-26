import pytest
from fastapi.testclient import TestClient

from empresa.api import app

ANA = {
    "cpf": "529.982.247-25",
    "pnome": "Ana",
    "unome": "Lima",
    "salario": "4200.50",
    "departamento_id": 5,
}


@pytest.fixture
def cliente(banco_teste, dados):
    with TestClient(app) as c:  # executa o lifespan: abre e fecha o pool
        yield c


def test_dados_invalidos_retorna_422(cliente):
    r = cliente.post(
        "/funcionarios",
        json={"cpf": "123", "pnome": "Ana", "unome": "Lima", "salario": "-1", "departamento_id": 5},
    )
    assert r.status_code == 422
    assert r.json()["erros"] == [
        "body.cpf: CPF deve ter 11 dígitos",
        "body.salario: deve ser maior que 0",
    ]


def test_inexistente_retorna_404(cliente):
    assert cliente.get("/funcionarios/999").status_code == 404
    assert cliente.get("/funcionarios/cpf/52998224725").status_code == 404


def test_cpf_malformado_na_url_retorna_422(cliente):
    r = cliente.get("/funcionarios/cpf/123")
    assert r.status_code == 422
    assert r.json()["erros"] == ["cpf: CPF deve ter 11 dígitos"]


def test_criar_obter_pelos_dois_caminhos_e_duplicar(cliente):
    r = cliente.post("/funcionarios", json=ANA)
    assert r.status_code == 201
    criado = r.json()
    assert (criado["id"], criado["cpf"]) == (9, "52998224725")
    assert cliente.get("/funcionarios/9").json() == criado
    assert cliente.get("/funcionarios/cpf/529.982.247-25").json() == criado
    assert cliente.post("/funcionarios", json=ANA).status_code == 409


def test_supervisor_por_cpf_no_corpo(cliente):
    r = cliente.post("/funcionarios", json=ANA | {"supervisor": {"cpf": "33344555587"}})
    assert r.status_code == 201
    assert r.json()["supervisor_id"] == 2


def test_referencia_com_id_e_cpf_juntos_retorna_422(cliente):
    r = cliente.put("/departamentos/4/gerente", json={"id": 1, "cpf": "12345678966"})
    assert r.status_code == 422
    assert "informe o id ou o CPF" in r.json()["erros"][0]


def test_listar_com_filtro_e_paginacao(cliente):
    r = cliente.get("/funcionarios", params={"dep": 5, "limite": 3, "pagina": 2})
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_limite_fora_do_intervalo(cliente):
    r = cliente.get("/funcionarios", params={"limite": 500})
    assert r.status_code == 422
    assert r.json()["erros"] == ["query.limite: deve ser menor ou igual a 100"]


def test_regra_de_negocio_retorna_422(cliente):
    r = cliente.post(
        "/alocacoes", json={"funcionario": {"cpf": "12345678966"}, "projeto_id": 3, "horas": "1"}
    )
    assert r.status_code == 422


def test_relatorio_departamentos(cliente):
    r = cliente.get("/relatorios/departamentos")
    assert r.status_code == 200
    assert [d["id"] for d in r.json()] == [1, 4, 5, 6]


def test_relatorio_equipes(cliente):
    r = cliente.get("/relatorios/equipes", params={"max_func": 0})
    assert r.status_code == 200
    assert r.json() == [
        {
            "id": 40,
            "projnome": "Portal do Cliente",
            "dnome": "Matriz",
            "qtd_func": 0,
            "total_horas": "0",
        }
    ]


def test_relatorio_equipes_exige_parametro(cliente):
    assert cliente.get("/relatorios/equipes").status_code == 422


def test_relatorio_dependentes(cliente):
    r = cliente.get("/relatorios/dependentes", params={"min": 3})
    assert [d["nome"] for d in r.json()] == ["Fernando T Wong", "João B Silva"]


def test_esquema_ausente_retorna_503(banco_descartavel, monkeypatch):
    monkeypatch.setenv("PGDATABASE", banco_descartavel())  # banco vazio
    with TestClient(app) as c:
        r = c.get("/departamentos")
    assert r.status_code == 503
    assert "empresa banco criar" in r.json()["erros"][0]
