from decimal import Decimal

from empresa.repositorios import AlocacaoRepositorio, FuncionarioRepositorio


def test_obter_funcionario(conn):
    f = FuncionarioRepositorio(conn).obter("33344555587")
    assert f.nome == "Fernando T Wong"
    assert f.salario == Decimal("40000.00")


def test_obter_inexistente_devolve_none(conn):
    assert FuncionarioRepositorio(conn).obter("00000000000") is None


def test_buscar_filtra_e_pagina_no_banco(conn):
    repo = FuncionarioRepositorio(conn)
    pag1 = repo.buscar(dnr=5, limite=3)
    pag2 = repo.buscar(dnr=5, limite=3, offset=3)
    assert len(pag1) == 3 and len(pag2) == 1
    assert {f.cpf for f in pag1}.isdisjoint({f.cpf for f in pag2})


def test_buscar_trata_curinga_digitado_como_literal(conn):
    assert FuncionarioRepositorio(conn).buscar(nome="%") == []


def test_mudanca_e_revertida_ao_fim_do_teste(conn):
    repo = FuncionarioRepositorio(conn)
    assert repo.mudar_departamento("12345678966", 4)
    assert repo.obter("12345678966").dnr == 4


def test_carga_semanal(conn):
    assert AlocacaoRepositorio(conn).carga_semanal("12345678966") == Decimal("40.0")
