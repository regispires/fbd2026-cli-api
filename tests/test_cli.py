import pytest

from empresa.cli import main


def test_listar_departamentos(banco_teste, dados, capsys):
    main(["departamento", "listar"])
    saida = capsys.readouterr().out
    assert "Pesquisa" in saida and "Administração" in saida


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


def test_uso_incorreto_sai_com_codigo_2():
    with pytest.raises(SystemExit) as exc:
        main(["funcionario"])
    assert exc.value.code == 2
