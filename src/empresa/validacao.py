"""Funções puras de validação e normalização.

Levantam ValueError para que o Pydantic as reaproveite nos validadores e
agregue o erro aos demais campos.
"""

import re


def normalizar_cpf(cpf: str) -> str:
    # remove a máscara e confere só o formato: usado para CPFs que referenciam
    # funcionários já cadastrados (a existência é conferida pelo banco)
    d = re.sub(r"\D", "", cpf or "")
    if len(d) != 11:
        raise ValueError("CPF deve ter 11 dígitos")
    return d


def validar_cpf(cpf: str) -> str:
    # usado no cadastro de um funcionário novo: confere os dígitos verificadores
    d = normalizar_cpf(cpf)
    if d == d[0] * 11:
        raise ValueError("CPF deve ter 11 dígitos válidos")
    for n in (9, 10):
        soma = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        if soma * 10 % 11 % 10 != int(d[n]):
            raise ValueError("dígito verificador do CPF inválido")
    return d


def normalizar_decimal(texto: str) -> str:
    # aceita 4.200,50 ou 4200.50 digitados na CLI
    texto = texto.strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return texto


def escapar_like(texto: str) -> str:
    # % e _ digitados pelo usuário viram caracteres literais no LIKE/ILIKE
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
