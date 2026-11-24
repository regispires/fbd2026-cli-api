import pytest
from fastapi.testclient import TestClient

from empresa.api import app


@pytest.fixture
def cliente(banco_teste, dados):
    with TestClient(app) as c:  # executa o lifespan: abre e fecha o pool
        yield c


def test_dados_invalidos_retorna_422(cliente):
    r = cliente.post(
        "/funcionarios",
        json={"cpf": "123", "pnome": "Ana", "unome": "Lima", "salario": "-1", "dnr": 5},
    )
    assert r.status_code == 422
    assert r.json()["erros"] == [
        "body.cpf: CPF deve ter 11 dígitos",
        "body.salario: deve ser maior que 0",
    ]


def test_inexistente_retorna_404(cliente):
    r = cliente.get("/funcionarios/52998224725")
    assert r.status_code == 404


def test_criar_obter_e_duplicar(cliente):
    novo = {
        "cpf": "529.982.247-25",
        "pnome": "Ana",
        "unome": "Lima",
        "salario": "4200.50",
        "dnr": 5,
    }
    r = cliente.post("/funcionarios", json=novo)
    assert r.status_code == 201
    assert r.json()["cpf"] == "52998224725"
    assert cliente.get("/funcionarios/52998224725").status_code == 200
    r = cliente.post("/funcionarios", json=novo)
    assert r.status_code == 409


def test_listar_com_filtro_e_paginacao(cliente):
    r = cliente.get("/funcionarios", params={"dep": 5, "limite": 3, "pagina": 2})
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_limite_fora_do_intervalo(cliente):
    r = cliente.get("/funcionarios", params={"limite": 500})
    assert r.status_code == 422
    assert r.json()["erros"] == ["query.limite: deve ser menor ou igual a 100"]


def test_regra_de_negocio_retorna_422(cliente):
    r = cliente.post("/alocacoes", json={"cpf": "12345678966", "projnumero": 3, "horas": "1"})
    assert r.status_code == 422


def test_relatorio_departamentos(cliente):
    r = cliente.get("/relatorios/departamentos")
    assert r.status_code == 200
    assert len(r.json()) == 3
