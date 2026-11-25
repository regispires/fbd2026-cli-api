from decimal import Decimal

from empresa.repositorios import AlocacaoRepositorio, FuncionarioRepositorio

FERNANDO = 2


def test_obter_funcionario_por_id(conn):
    f = FuncionarioRepositorio(conn).obter(FERNANDO)
    assert (f.cpf, f.nome, f.salario) == ("33344555587", "Fernando T Wong", Decimal("40000.00"))


def test_obter_por_cpf_e_id_por_cpf(conn):
    repo = FuncionarioRepositorio(conn)
    assert repo.obter_por_cpf("33344555587").id == FERNANDO
    assert repo.id_por_cpf("33344555587") == FERNANDO


def test_obter_inexistente_devolve_none(conn):
    repo = FuncionarioRepositorio(conn)
    assert repo.obter(999) is None
    assert repo.id_por_cpf("00000000000") is None


def test_buscar_filtra_e_pagina_no_banco(conn):
    repo = FuncionarioRepositorio(conn)
    pag1 = repo.buscar(departamento_id=5, limite=3)
    pag2 = repo.buscar(departamento_id=5, limite=3, offset=3)
    assert len(pag1) == 3 and len(pag2) == 1
    assert {f.id for f in pag1}.isdisjoint({f.id for f in pag2})


def test_buscar_trata_curinga_digitado_como_literal(conn):
    assert FuncionarioRepositorio(conn).buscar(nome="%") == []


def test_mudanca_e_revertida_ao_fim_do_teste(conn):
    repo = FuncionarioRepositorio(conn)
    assert repo.mudar_departamento(1, 4)
    assert repo.obter(1).departamento_id == 4


def test_carga_semanal(conn):
    assert AlocacaoRepositorio(conn).carga_semanal(1) == Decimal("40.0")
