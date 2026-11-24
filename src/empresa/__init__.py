"""Aplicação de referência: integração entre PostgreSQL e Python com Psycopg 3.

Camadas:
    cli.py, api.py          apresentação (linha de comando e web)
    servicos/               regras de negócio e fronteira das transações
    repositorios/           SQL explícito e mapeamento de linhas
    consultas/              arquivos .sql carregados por sql_de()
    dto.py, validacao.py    modelos de entrada (Pydantic) e de saída (dataclasses)
"""
