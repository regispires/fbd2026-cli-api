from decimal import Decimal

import pytest
from pydantic import ValidationError

from empresa.dto import FuncionarioAlteracao, FuncionarioNovo, FuncionarioRef
from empresa.mensagens import mensagens
from empresa.validacao import escapar_like, normalizar_cpf, normalizar_decimal, validar_cpf


def test_validar_cpf_remove_mascara():
    assert validar_cpf("529.982.247-25") == "52998224725"


@pytest.mark.parametrize("cpf", ["123", "11111111111", "52998224724"])
def test_validar_cpf_rejeita(cpf):
    with pytest.raises(ValueError):
        validar_cpf(cpf)


def test_normalizar_cpf_aceita_cpf_do_livro():
    # CPF de referência: só o formato é conferido
    assert normalizar_cpf("123.456.789-66") == "12345678966"


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [("4.200,50", "4200.50"), ("4200.50", "4200.50"), (" 3000 ", "3000")],
)
def test_normalizar_decimal(texto, esperado):
    assert normalizar_decimal(texto) == esperado


def test_escapar_like():
    assert escapar_like("50%_a") == "50\\%\\_a"


def test_modelo_reune_todos_os_erros_em_portugues():
    with pytest.raises(ValidationError) as exc:
        FuncionarioNovo(
            cpf="123", pnome="", unome="Lima", salario="-1", departamento_id="x", sexo="Z"
        )
    assert mensagens(exc.value.errors()) == [
        "cpf: CPF deve ter 11 dígitos",
        "pnome: não pode ficar vazio",
        "salario: deve ser maior que 0",
        "departamento_id: número inteiro inválido",
        "sexo: valores aceitos: 'M' ou 'F'",
    ]


def test_modelo_converte_tipos():
    f = FuncionarioNovo(
        cpf="529.982.247-25", pnome=" Ana ", unome="Lima", salario="4200.5", departamento_id="5"
    )
    assert (f.cpf, f.pnome, f.salario, f.departamento_id) == (
        "52998224725",
        "Ana",
        Decimal("4200.5"),
        5,
    )


@pytest.mark.parametrize(
    ("dados", "descricao"), [({"id": 3}, "id 3"), ({"cpf": "123.456.789-66"}, "CPF 12345678966")]
)
def test_referencia_por_id_ou_cpf(dados, descricao):
    assert FuncionarioRef(**dados).descricao() == descricao


@pytest.mark.parametrize("dados", [{}, {"id": 3, "cpf": "12345678966"}])
def test_referencia_exige_exatamente_um(dados):
    with pytest.raises(ValidationError) as exc:
        FuncionarioRef(**dados)
    assert "informe o id ou o CPF do funcionário" in mensagens(exc.value.errors())[0]


def test_alteracao_parcial_traz_so_o_informado():
    alt = FuncionarioAlteracao(salario="4500")
    assert alt.model_dump(exclude_unset=True) == {"salario": Decimal("4500")}
