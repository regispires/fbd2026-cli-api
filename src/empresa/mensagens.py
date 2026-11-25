"""Tradução para português dos erros de validação do Pydantic.

Serve à CLI (ValidationError.errors()) e à API (RequestValidationError.errors()),
que produzem a mesma lista de dicionários.
"""

MSG = {
    "missing": "campo obrigatório",
    "greater_than": "deve ser maior que {gt}",
    "greater_than_equal": "deve ser maior ou igual a {ge}",
    "less_than_equal": "deve ser menor ou igual a {le}",
    "string_too_short": "não pode ficar vazio",
    "string_too_long": "até {max_length} caracteres",
    "decimal_max_digits": "até {max_digits} dígitos",
    "decimal_max_places": "até {decimal_places} casas",
    "int_parsing": "número inteiro inválido",
    "decimal_parsing": "número decimal inválido",
    "date_from_datetime_parsing": "data inválida (use AAAA-MM-DD)",
    "literal_error": "valores aceitos: {expected}",
    "value_error": "{error}",
}


def mensagens(erros) -> list[str]:
    saida = []
    for err in erros:
        campo = ".".join(map(str, err["loc"]))
        modelo = MSG.get(err["type"], err["msg"])
        texto = modelo.format(**err.get("ctx", {})).replace("' or '", "' ou '")
        # erro do modelo inteiro (model_validator) não tem campo
        saida.append(campo + ": " + texto if campo else texto)
    return saida
