# fbd2026-simples

Aplicação de referência do módulo **Integração entre PostgreSQL e aplicações Python**.
Gerencia funcionários, departamentos, projetos e alocações do esquema EMPRESA, com
SQL explícito via Psycopg 3, transações controladas pela aplicação e duas interfaces
sobre o mesmo núcleo: linha de comando (argparse) e web (FastAPI, opcional).

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/): gerencia o projeto, as dependências e o Python.
  Se o Python 3.12 (de `.python-version`) não estiver instalado, o uv o baixa.
- Docker com Docker Compose, ou um PostgreSQL 14 ou superior já instalado.

## Instalação

```bash
git clone https://github.com/regispires/fbd2026-simples.git
cd fbd2026-simples
uv sync --locked
cp .env.example .env
```

Edite o `.env` e troque a senha. O mesmo arquivo serve ao Docker Compose e à aplicação.

## Banco de dados

Com Docker Compose (os scripts de `sql/` rodam na primeira criação do volume, em ordem):

```bash
docker compose up -d --wait
```

Sem Docker, num PostgreSQL existente:

```bash
psql -d empresa -f sql/01_esquema.sql
psql -d empresa -f sql/02_visoes.sql
psql -d empresa -f sql/03_dados_exemplo.sql
```

Para recriar o banco do zero com Compose: `docker compose down -v` e depois `docker compose up -d --wait`.

## Execução pela linha de comando

Todos os comandos recebem as variáveis do `.env` com `--env-file`. Para não repetir a opção,
defina `UV_ENV_FILE=.env` na sessão do terminal.

```bash
uv run --env-file .env empresa --help
```

Funcionários (CRUD, filtros e paginação no banco):

```bash
uv run --env-file .env empresa funcionario listar --dep 5 --nome silva --salario-min 30000 --limite 20 --pagina 1
uv run --env-file .env empresa funcionario obter 33344555587
uv run --env-file .env empresa funcionario criar --cpf 529.982.247-25 --pnome Ana --unome Lima --salario "4.200,50" --dep 5 --sexo F
uv run --env-file .env empresa funcionario atualizar 52998224725 --salario 4500 --endereco "Rua A, 10"
uv run --env-file .env empresa funcionario remover 52998224725
```

Departamentos e projetos:

```bash
uv run --env-file .env empresa departamento listar
uv run --env-file .env empresa departamento criar --numero 6 --nome Logística
uv run --env-file .env empresa departamento renomear 6 --nome Suprimentos
uv run --env-file .env empresa departamento trocar-gerente 4 --cpf 99988777767
uv run --env-file .env empresa projeto criar --nome ProdutoW --local Fortaleza --dep 5
uv run --env-file .env empresa projeto atualizar 31 --local Quixadá
uv run --env-file .env empresa projeto listar --dep 5
```

Alocações (operações transacionais):

```bash
uv run --env-file .env empresa alocacao criar --cpf 98765432168 --projeto 10 --horas 5
uv run --env-file .env empresa alocacao equipe --projeto 1 --arquivo equipe.csv
uv run --env-file .env empresa alocacao listar --projeto 10
```

O arquivo da equipe tem uma linha `cpf;horas` por funcionário, por exemplo `52998224725;3,5`.

Relatórios (consultas de negócio):

```bash
uv run --env-file .env empresa relatorio departamentos
uv run --env-file .env empresa relatorio ranking --dep 4 5
uv run --env-file .env empresa relatorio todos-projetos
uv run --env-file .env empresa relatorio supervisao 88866555576
uv run --env-file .env empresa relatorio exportar funcionarios.csv
```

A opção global `--json` troca a tabela por JSON: `empresa --json departamento listar`.

Códigos de saída: `0` sucesso, `1` erro de validação ou de regra, `2` uso incorreto,
`3` banco de dados indisponível.

Exemplo de saída esperada:

```text
$ uv run --env-file .env empresa alocacao criar --cpf 12345678966 --projeto 3 --horas 12
Erro: Carga semanal de 12345678966 passaria de 40 h (atual: 40.0 h)

$ uv run --env-file .env empresa funcionario criar --cpf 123 --pnome "" --unome Lima --salario -1 --dep x
Dados inválidos:
cpf: CPF deve ter 11 dígitos
pnome: não pode ficar vazio
salario: deve ser maior que 0
dnr: número inteiro inválido
```

## Execução pela web (opcional)

```bash
uv run --env-file .env fastapi dev src/empresa/api.py
```

A documentação interativa fica em <http://127.0.0.1:8000/docs>. Principais rotas:

| Método e rota | Operação |
|---|---|
| `POST /funcionarios`, `GET /funcionarios?dep=5&nome=silva&limite=20&pagina=1` | criar, listar com filtros |
| `GET`, `PATCH`, `DELETE /funcionarios/{cpf}` | obter, atualizar parcialmente, excluir |
| `POST`, `GET /departamentos`; `GET`, `PATCH`, `DELETE /departamentos/{n}` | CRUD de departamentos |
| `PUT /departamentos/{n}/gerente` | trocar gerente (transação) |
| `POST`, `GET /projetos`; `GET`, `PATCH`, `DELETE /projetos/{n}` | CRUD de projetos |
| `POST /alocacoes`, `DELETE /alocacoes/{cpf}/{n}`, `GET /projetos/{n}/alocacoes` | alocações |
| `GET /relatorios/departamentos`, `/ranking?dep=4`, `/todos-projetos`, `/supervisao/{cpf}` | relatórios |

Erros de domínio viram status HTTP (404 não encontrado, 409 duplicidade ou referência,
422 dados inválidos ou regra violada), sempre no formato `{"erros": [...]}` em português.

## Testes

```bash
uv run --env-file .env pytest
uv run ruff check .
```

Os testes usam um PostgreSQL real: criam um banco descartável `empresa_teste_*` com o esquema
e as visões, recarregam os dados de exemplo antes de cada teste de serviço e removem o banco
ao final. O usuário do `.env` precisa poder criar bancos (o usuário do Compose pode). Os testes
de repositório rodam dentro de uma transação revertida ao fim de cada teste.

## Estrutura

```text
fbd2026-simples/
├── pyproject.toml           # dependências e o comando empresa
├── uv.lock                  # versões exatas, versionado
├── .python-version          # versão do Python usada pelo uv
├── compose.yaml  .env.example  README.md
├── sql/
│   ├── 01_esquema.sql       # tabelas, restrições nomeadas, índices
│   ├── 02_visoes.sql        # vw_funcionario_depto, vw_resumo_departamento
│   └── 03_dados_exemplo.sql
├── src/empresa/
│   ├── cli.py               # interface de linha de comando
│   ├── api.py               # interface web (FastAPI, opcional)
│   ├── config.py  db.py     # configuração do ambiente e pool de conexões
│   ├── dto.py               # modelos de entrada (Pydantic) e de saída (dataclasses)
│   ├── validacao.py         # CPF, decimal com vírgula, curingas do LIKE
│   ├── erros.py             # exceções de domínio e tradução dos erros do banco
│   ├── mensagens.py         # erros de validação em português
│   ├── consultas/           # arquivos .sql e sql_de()
│   ├── repositorios/        # SQL e mapeamento: funcionario, departamento, projeto, ...
│   └── servicos/            # regras de negócio e transações
└── tests/
    ├── conftest.py          # banco de teste, dados recarregados, transação revertida
    ├── test_validacao.py  test_repositorios.py  test_servicos.py
    └── test_api.py  test_cli.py
```

## Requisitos da etapa final atendidos

| Requisito | Onde |
|---|---|
| Conexão ao PostgreSQL | `db.py` (pool) e `config.py` |
| Configuração externa | variáveis `PG*` no `.env`, carregadas com `uv run --env-file` |
| CRUD de três recursos | funcionário, departamento e projeto (`servicos/`, `repositorios/`) |
| Validação de entradas | modelos Pydantic em `dto.py` e funções de `validacao.py` |
| Quatro consultas de negócio | `consultas/rel_*.sql`: resumo por departamento, ranking salarial, divisão relacional, supervisão recursiva |
| Visão | `vw_resumo_departamento` e `vw_funcionario_depto` |
| Operação transacional | `AlocacaoServico.alocar` (limite de 40 h com `FOR UPDATE`), `alocar_equipe` (savepoints), `DepartamentoServico.trocar_gerente` |
| Consultas parametrizadas | todo valor vai como parâmetro; identificadores dinâmicos com `psycopg.sql` |
| Erros de integridade | `erros.traduzir` usa o nome da restrição violada |
| Paginação e filtragem no banco | `FuncionarioRepositorio.buscar` (WHERE composto, LIMIT e OFFSET) |
| Instalação e execução | este README |

## Decisões de projeto

- **SQL explícito, sem ORM.** As consultas ficam em `src/empresa/consultas/*.sql`, testáveis no psql.
- **Três camadas.** A apresentação (CLI ou API) monta modelos e chama serviços; os serviços abrem
  a transação e aplicam as regras; os repositórios só executam SQL e mapeiam linhas.
- **Pydantic só na entrada.** As saídas são dataclasses preenchidas por `class_row`, sem revalidar
  o que o banco já garante.
- **CPF novo e CPF de referência.** O cadastro de funcionário confere os dígitos verificadores.
  Onde o CPF só referencia alguém já cadastrado (alocação, gerente, supervisor), confere-se o
  formato e o banco verifica a existência. Assim os dados do livro, cujos CPFs não têm dígitos
  válidos, continuam utilizáveis.
- **Restrições nomeadas no banco** são a última barreira; a aplicação antecipa a validação para
  responder com mensagens do domínio.

## Limitações conhecidas

- A listagem de funcionários pagina com `LIMIT/OFFSET`, mais simples para CLI e API. Para tabelas
  grandes, a paginação por chave (keyset) é mais eficiente.
- A regra das 40 horas semanais é aplicada pela aplicação. Outro cliente que escreva direto no
  banco não passa por ela.
- No livro, Jorge Brito aparece no projeto 20 com horas nulas. Como `horas` é `NOT NULL` aqui, essa
  linha foi omitida dos dados de exemplo.
- Não há autenticação na API.
