import psycopg
import pytest

from empresa import banco
from empresa.config import carregar
from empresa.erros import RegraViolada


def contar(conninfo: str, consulta: str):
    with psycopg.connect(conninfo) as c:
        return c.execute(consulta).fetchone()[0]


def test_criar_banco_so_cria_uma_vez(banco_descartavel):
    nome = banco_descartavel()  # a fábrica já o criou
    assert banco.criar_banco(carregar().conninfo, nome) is False


def test_criar_esquema_e_recriar(conninfo_vazio):
    banco.criar_esquema(conninfo_vazio)
    banco.povoar(conninfo_vazio)
    with pytest.raises(RegraViolada, match="--recriar"):
        banco.criar_esquema(conninfo_vazio)
    banco.criar_esquema(conninfo_vazio, recriar=True)
    assert contar(conninfo_vazio, "SELECT count(*) FROM funcionario") == 0


def test_falha_no_meio_desfaz_todo_o_esquema(conninfo_vazio, monkeypatch):
    original = banco.script

    def script_com_erro(nome):
        if nome == "02_visoes.sql":
            return "CREATE VIEW vw_quebrada AS SELECT * FROM tabela_inexistente;"
        return original(nome)

    monkeypatch.setattr(banco, "script", script_com_erro)
    with pytest.raises(psycopg.errors.UndefinedTable):
        banco.criar_esquema(conninfo_vazio)
    # as tabelas do 01_esquema.sql também foram desfeitas: tudo ou nada
    assert contar(conninfo_vazio, "SELECT to_regclass('funcionario')") is None


def test_povoar_exige_esquema(conninfo_vazio):
    with pytest.raises(RegraViolada, match="banco criar"):
        banco.povoar(conninfo_vazio)


def test_povoar_nao_duplica_e_limpar_substitui(conninfo_vazio):
    banco.criar_esquema(conninfo_vazio)
    assert banco.povoar(conninfo_vazio) == 8
    with pytest.raises(RegraViolada, match="--limpar"):
        banco.povoar(conninfo_vazio)
    assert banco.povoar(conninfo_vazio, limpar=True) == 8
    # RESTART IDENTITY: os ids voltam a ser os mesmos
    assert contar(conninfo_vazio, "SELECT max(id) FROM funcionario") == 8


def test_falha_na_carga_preserva_os_dados_anteriores(conninfo_vazio, monkeypatch):
    banco.criar_esquema(conninfo_vazio)
    banco.povoar(conninfo_vazio)
    original = banco.script

    def carga_com_erro(nome):
        if nome == "03_dados_exemplo.sql":
            return "INSERT INTO projeto (projnome) VALUES ('sem departamento');"
        return original(nome)  # limpar_dados.sql roda de verdade

    monkeypatch.setattr(banco, "script", carga_com_erro)
    with pytest.raises(psycopg.errors.NotNullViolation):
        banco.povoar(conninfo_vazio, limpar=True)  # o TRUNCATE foi desfeito
    assert contar(conninfo_vazio, "SELECT count(*) FROM funcionario") == 8
