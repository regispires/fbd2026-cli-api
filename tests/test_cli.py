import pytest

from empresa.cli import main


def test_listar_departamentos(banco_teste, dados, capsys):
    main(["departamento", "listar"])
    saida = capsys.readouterr().out
    assert "Pesquisa" in saida and "Administração" in saida


@pytest.mark.parametrize("ref", [["--id", "2"], ["--cpf", "333.445.555-87"]])
def test_obter_funcionario_por_id_ou_cpf(banco_teste, dados, capsys, ref):
    main(["funcionario", "obter", *ref])
    assert "Fernando" in capsys.readouterr().out


def test_relatorio_equipes(banco_teste, dados, capsys):
    main(["relatorio", "equipes", "--max-func", "0"])
    saida = capsys.readouterr().out
    assert "Portal do Cliente" in saida and "ProdutoX" not in saida


def test_erro_de_dominio_sai_com_codigo_1(banco_teste, dados):
    with pytest.raises(SystemExit) as exc:
        main(["alocacao", "criar", "--cpf", "12345678966", "--projeto", "3", "--horas", "1"])
    assert "Carga semanal" in str(exc.value.code)


def test_validacao_lista_erros_em_portugues(banco_teste, dados):
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "funcionario",
                "criar",
                "--cpf",
                "123",
                "--pnome",
                "Ana",
                "--unome",
                "Lima",
                "--salario",
                "-1",
                "--dep",
                "5",
            ]
        )
    assert "salario: deve ser maior que 0" in str(exc.value.code)


@pytest.mark.parametrize(
    "argv",
    [
        ["funcionario"],
        ["funcionario", "obter"],
        ["funcionario", "obter", "--id", "1", "--cpf", "12345678966"],
    ],
)
def test_uso_incorreto_sai_com_codigo_2(argv):
    with pytest.raises(SystemExit) as exc:
        main(argv)
    assert exc.value.code == 2


def test_banco_criar_existente_pede_recriar(banco_teste):
    with pytest.raises(SystemExit) as exc:
        main(["banco", "criar"])
    assert "--recriar" in str(exc.value.code)


def test_banco_povoar_com_limpar(banco_teste, capsys):
    main(["banco", "povoar", "--limpar"])
    assert "8 funcionários" in capsys.readouterr().out


def test_esquema_ausente_orienta_criar(banco_descartavel, monkeypatch):
    monkeypatch.setenv("PGDATABASE", banco_descartavel())  # banco vazio
    with pytest.raises(SystemExit) as exc:
        main(["departamento", "listar"])
    assert "empresa banco criar" in str(exc.value.code)
