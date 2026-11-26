# fbd2026-cli-api

Aplicação de referência do módulo **Integração entre PostgreSQL e aplicações Python**.
Gerencia funcionários, departamentos, projetos e alocações do esquema EMPRESA, com
SQL explícito via Psycopg 3, transações controladas pela aplicação e duas interfaces
sobre o mesmo núcleo: linha de comando (argparse) e web (FastAPI).

O banco pode ser local, na nuvem ou no Docker, e o Docker é opcional: a aplicação só lê as
variáveis `PG*` do `.env`, e o código é o mesmo nos três casos. Com Docker, o Compose sobe o
banco e também a aplicação (veja [Onde fica o banco](#onde-fica-o-banco)).

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/): gerencia o projeto, as dependências e o Python.
  Se o Python 3.12 (de `.python-version`) não estiver instalado, o uv o baixa.
- Um servidor PostgreSQL 14 ou superior: local, na nuvem ou no Docker. O Docker é opcional.

## Instalação

```bash
git clone https://github.com/regispires/fbd2026-cli-api.git
cd fbd2026-cli-api
uv sync --locked
cp .env.example .env
```

Edite o `.env` com os dados do seu servidor e troque a senha. O mesmo arquivo serve à aplicação
e ao Docker Compose.

## Onde fica o banco

A aplicação usa o servidor indicado pelas variáveis `PG*` do `.env`, então o código é o mesmo em
qualquer modo. O `.env.example` traz um bloco para cada caso.

| Modo | Banco | Aplicação | Como subir o banco |
|---|---|---|---|
| Local | PostgreSQL instalado na máquina | `uv run` | já está no ar |
| Nuvem | Neon, Supabase, RDS etc. | `uv run` | já está no ar; use `PGSSLMODE=require` |
| Docker, só o banco | contêiner `db` | `uv run` | `docker compose up -d db` |
| Docker, tudo | contêiner `db` | contêiner `app` | `docker compose up -d` |

Na nuvem, prefira a conexão direta. Se usar um pooler em modo transação, ponha
`PREPARE_THRESHOLD=off` no `.env`, porque esse tipo de pooler não convive com os comandos que o
Psycopg prepara no servidor. Planos gratuitos limitam conexões: mantenha `POOL_MAX` baixo.

## Criação do esquema e dados de exemplo

Com o servidor no ar, crie o esquema e, se quiser, carregue os dados de exemplo:

```bash
uv run --env-file .env empresa banco criar     # cria o banco, se preciso, e o esquema
uv run --env-file .env empresa banco povoar    # opcional: dados de exemplo do livro
```

Cada comando roda numa única transação: ou tudo é aplicado, ou nada muda. O `criar` só cria o
banco se ele não existir, e isso fica fora da transação, porque `CREATE DATABASE` não pode rodar
dentro de uma. Na nuvem, o banco normalmente já existe. Os comandos se recusam a sobrescrever o
que já existe:

| Comando | Quando usar |
|---|---|
| `empresa banco criar --recriar` | apagar tabelas e visões e criá-las de novo (os dados se perdem) |
| `empresa banco povoar --limpar` | trocar os dados atuais pelos de exemplo, com os ids reiniciados |

Antes do `criar`, a CLI e a API respondem que o esquema não existe (a API, com status 503). Os
scripts ficam em `src/empresa/sql/`. Também é possível aplicá-los direto no psql, cada um numa
transação, com `psql -1 -f src/empresa/sql/01_esquema.sql` e assim por diante.

## Tudo no Docker

O `compose.yaml` compõe dois serviços. O `db` é o PostgreSQL, com volume e verificação de saúde.
O `app` é a aplicação, construída pelo `Dockerfile` com o `uv.lock`: sobe a API na porta 8000 e
traz também a CLI.

```bash
docker compose up -d                              # banco e aplicação
docker compose exec app empresa banco criar       # a CLI roda dentro do contêiner da aplicação
docker compose exec app empresa banco povoar      # opcional
```

A API fica em <http://localhost:8000/docs>. Alguns pontos que o Compose resolve:

- **Ordem de inicialização:** o `app` só sobe depois que o `db` aceita conexões
  (`depends_on` com `condition: service_healthy`).
- **Rede interna:** dentro do Compose, a aplicação acha o banco pelo nome do serviço. O `.env`
  continua com `PGHOST=localhost`, para quem roda a aplicação na máquina, e o `compose.yaml`
  troca para `PGHOST=db` só no contêiner.
- **Portas publicadas:** a 5432 do banco e a 8000 da API ficam acessíveis na máquina.

Depois de mudar o código, reconstrua a imagem com `docker compose up -d --build`. Para apagar o
banco junto com o volume, use `docker compose down -v`.

## Execução pela linha de comando

Todos os comandos recebem as variáveis do `.env` com `--env-file`. Para não repetir a opção,
defina `UV_ENV_FILE=.env` na sessão do terminal.

```bash
uv run --env-file .env empresa --help
```

Funcionários (CRUD, filtros e paginação no banco). Todo comando que aponta para um funcionário
aceita `--id` ou `--cpf`, um dos dois:

```bash
uv run --env-file .env empresa funcionario listar --dep 5 --nome silva --salario-min 30000 --limite 20 --pagina 1
uv run --env-file .env empresa funcionario obter --id 2
uv run --env-file .env empresa funcionario obter --cpf 333.445.555-87
uv run --env-file .env empresa funcionario criar --cpf 529.982.247-25 --pnome Ana --unome Lima --salario "4.200,50" --dep 5 --sexo F --supervisor-cpf 33344555587
uv run --env-file .env empresa funcionario atualizar --id 9 --salario 4500 --endereco "Rua A, 10"
uv run --env-file .env empresa funcionario remover --cpf 52998224725
```

Departamentos e projetos são identificados pelo `id` gerado pelo banco:

```bash
uv run --env-file .env empresa departamento listar
uv run --env-file .env empresa departamento criar --nome Logística
uv run --env-file .env empresa departamento renomear 7 --nome Suprimentos
uv run --env-file .env empresa departamento trocar-gerente 4 --cpf 99988777767
uv run --env-file .env empresa departamento trocar-gerente 4 --funcionario-id 3
uv run --env-file .env empresa projeto criar --nome ProdutoW --local Fortaleza --dep 5
uv run --env-file .env empresa projeto atualizar 41 --local Quixadá
uv run --env-file .env empresa projeto listar --dep 5
```

Alocações (operações transacionais):

```bash
uv run --env-file .env empresa alocacao criar --cpf 98765432168 --projeto 10 --horas 5
uv run --env-file .env empresa alocacao criar --funcionario-id 4 --projeto 10 --horas 5
uv run --env-file .env empresa alocacao equipe --projeto 1 --arquivo equipe.csv
uv run --env-file .env empresa alocacao listar --projeto 10
uv run --env-file .env empresa alocacao remover --funcionario-id 4 --projeto 10
```

O arquivo da equipe é um CSV com `;` e cabeçalho `cpf;horas` ou `id;horas`, por exemplo:

```text
cpf;horas
52998224725;3,5
12345678966;2
```

Relatórios (consultas de negócio):

```bash
uv run --env-file .env empresa relatorio departamentos
uv run --env-file .env empresa relatorio ranking --dep 4 5
uv run --env-file .env empresa relatorio todos-projetos
uv run --env-file .env empresa relatorio equipes --max-func 2
uv run --env-file .env empresa relatorio dependentes --min 0
uv run --env-file .env empresa relatorio supervisao --cpf 88866555576
uv run --env-file .env empresa relatorio exportar funcionarios.csv
```

A opção global `--json` troca a tabela por JSON: `empresa --json departamento listar`.

Códigos de saída: `0` sucesso, `1` erro de validação ou de regra, `2` uso incorreto,
`3` banco de dados indisponível.

Exemplo de saída esperada:

```text
$ uv run --env-file .env empresa alocacao criar --cpf 12345678966 --projeto 3 --horas 1
Erro: Carga semanal do funcionário (CPF 12345678966) passaria de 40 h (atual: 40.0 h)

$ uv run --env-file .env empresa relatorio supervisao --id 8
Jorge Brito (id 8, CPF 88866555576)
├── Fernando Wong (id 2, CPF 33344555587)
│   ├── Joice Leite (id 6, CPF 45345345376)
│   ├── João Silva (id 1, CPF 12345678966)
│   └── Ronaldo Lima (id 5, CPF 66688444476)
└── Jennifer Souza (id 4, CPF 98765432168)
    ├── Alice Zelaya (id 3, CPF 99988777767)
    └── André Pereira (id 7, CPF 98798798733)
```

## Execução pela web (opcional)

```bash
uv run --env-file .env fastapi dev src/empresa/api.py
```

O `fastapi dev` recarrega o código a cada alteração. No Docker, a API já sobe com o serviço `app`
(veja Tudo no Docker). A documentação interativa fica em <http://127.0.0.1:8000/docs>. Principais rotas:

| Método e rota | Operação |
|---|---|
| `POST /funcionarios`, `GET /funcionarios?dep=5&nome=silva&limite=20&pagina=1` | criar, listar com filtros |
| `GET`, `PATCH`, `DELETE /funcionarios/{id}` | obter, atualizar parcialmente, excluir pelo id |
| `GET`, `PATCH`, `DELETE /funcionarios/cpf/{cpf}` | as mesmas operações pelo CPF |
| `POST`, `GET /departamentos`; `GET`, `PATCH`, `DELETE /departamentos/{id}` | CRUD de departamentos |
| `PUT /departamentos/{id}/gerente` com corpo `{"id": 3}` ou `{"cpf": "..."}` | trocar gerente (transação) |
| `POST`, `GET /projetos`; `GET`, `PATCH`, `DELETE /projetos/{id}` | CRUD de projetos |
| `POST /alocacoes`, `GET /projetos/{id}/alocacoes` | alocar, listar alocações do projeto |
| `DELETE /alocacoes/{funcionario_id}/{projeto_id}`, `DELETE /alocacoes/cpf/{cpf}/{projeto_id}` | desalocar |
| `GET /relatorios/departamentos`, `/ranking?dep=4`, `/todos-projetos` | relatórios |
| `GET /relatorios/equipes?max_func=2`, `/relatorios/dependentes?min=0` | relatórios com LEFT JOIN e HAVING |
| `GET /relatorios/supervisao/{id}`, `/relatorios/supervisao/cpf/{cpf}` | árvore de supervisão |

Onde o corpo aponta para um funcionário, use um objeto com `id` ou `cpf`:

```json
{"funcionario": {"cpf": "98765432168"}, "projeto_id": 10, "horas": "5"}
```

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
fbd2026-cli-api/
├── pyproject.toml           # dependências e o comando empresa
├── uv.lock                  # versões exatas, versionado
├── .python-version          # versão do Python usada pelo uv
├── compose.yaml             # serviços db e app (Docker opcional)
├── Dockerfile  .dockerignore   # imagem da aplicação, com uv
├── .env.example  README.md
├── src/empresa/
│   ├── cli.py               # interface de linha de comando
│   ├── api.py               # interface web (FastAPI, opcional)
│   ├── config.py  db.py     # configuração do ambiente e pool de conexões
│   ├── dto.py               # modelos de entrada (Pydantic) e de saída (dataclasses)
│   ├── validacao.py         # CPF, decimal com vírgula, curingas do LIKE
│   ├── erros.py             # exceções de domínio e tradução dos erros do banco
│   ├── mensagens.py         # erros de validação em português
│   ├── banco.py             # criação do banco e do esquema, carga dos dados
│   ├── sql/                 # 01_esquema, 02_visoes, 03_dados_exemplo, remover, limpar_dados
│   ├── consultas/           # arquivos .sql e sql_de()
│   ├── repositorios/        # SQL e mapeamento: funcionario, departamento, projeto, ...
│   └── servicos/            # regras de negócio e transações
└── tests/
    ├── conftest.py          # banco de teste, dados recarregados, transação revertida
    ├── test_validacao.py  test_repositorios.py  test_servicos.py
    └── test_banco.py  test_api.py  test_cli.py
```

## Requisitos da etapa final atendidos

| Requisito | Onde |
|---|---|
| Conexão ao PostgreSQL | `db.py` (pool) e `config.py` |
| Configuração externa | variáveis `PG*` no `.env`, carregadas com `uv run --env-file` |
| CRUD de três recursos | funcionário, departamento e projeto (`servicos/`, `repositorios/`) |
| Validação de entradas | modelos Pydantic em `dto.py` e funções de `validacao.py` |
| Consultas de negócio | `consultas/rel_*.sql`: resumo por departamento, ranking salarial, divisão relacional, supervisão recursiva, projetos com equipe pequena, funcionários por número de dependentes |
| Junção externa | `LEFT JOIN` em `vw_resumo_departamento`, `vw_funcionario_depto` (supervisor), `rel_equipes.sql` e `rel_dependentes.sql` |
| Agrupamento com filtro | `GROUP BY ... HAVING` em `rel_equipes.sql` e `rel_dependentes.sql` |
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
- **Banco em qualquer lugar, Docker opcional.** A configuração vem só das variáveis `PG*`, e o
  esquema é sempre criado por `empresa banco criar`, em qualquer modo. O Compose não cria o
  esquema sozinho, para que criação e carga continuem passos explícitos.
- **Pydantic só na entrada.** As saídas são dataclasses preenchidas por `class_row`, sem revalidar
  o que o banco já garante.
- **Chaves substitutas.** As tabelas principais (`funcionario`, `departamento`, `projeto`,
  `dependente`) têm `id BIGINT GENERATED ALWAYS AS IDENTITY` como chave primária, sem
  significado e gerada pelo banco. As chaves estrangeiras apontam para esses ids. O CPF continua
  obrigatório e único (`uq_func_cpf`), assim como os nomes de departamento e de projeto, porque
  a chave natural ainda precisa ser garantida.
- **Funcionário por id ou por CPF.** O usuário raramente sabe o id de cor, então CLI e API aceitam
  os dois. `FuncionarioRef` exige exatamente um deles e o serviço converte o CPF no id antes de
  qualquer outra operação.
- **Ids do livro preservados.** Os dados de exemplo inserem departamentos (1, 4, 5) e projetos
  (1, 2, 3, 10, 20, 30) com `OVERRIDING SYSTEM VALUE` e depois ajustam a sequência com `setval`,
  para os números de Elmasri e Navathe continuarem valendo. O antigo `dnumero` deixou de existir:
  o id do departamento faz esse papel. Funcionários recebem ids gerados (1 a 8) e as ligações
  entre eles são feitas pelo CPF no script de carga.
- **CPF novo e CPF de referência.** O cadastro de funcionário confere os dígitos verificadores.
  Onde o CPF só referencia alguém já cadastrado (alocação, gerente, supervisor), confere-se o
  formato e o banco verifica a existência. Assim os dados do livro, cujos CPFs não têm dígitos
  válidos, continuam utilizáveis.
- **Restrições nomeadas no banco** são a última barreira; a aplicação antecipa a validação para
  responder com mensagens do domínio.

## Junções externas nos dados de exemplo

Os dados do livro já têm funcionários sem dependentes, sem projeto e sem supervisor. Para que
departamentos e projetos também tenham casos sem par, o script de carga acrescenta dois registros
fora do livro: o departamento 6 (Expansão), sem funcionários, projetos nem localização, e o projeto
40 (Portal do Cliente), sem ninguém alocado. Compare, por exemplo:

```bash
uv run --env-file .env empresa relatorio equipes --max-func 2   # Portal do Cliente aparece com 0
uv run --env-file .env empresa relatorio departamentos          # Expansão aparece com zeros
```

Nas duas consultas novas, `count(coluna_do_lado_opcional)` dá 0 para quem não tem par, enquanto
`count(*)` daria 1. O filtro sobre o total vai no `HAVING`, que é aplicado depois do agrupamento;
no `WHERE` ele não funcionaria, porque o `WHERE` roda antes do `GROUP BY`.

## Limitações conhecidas

- A listagem de funcionários pagina com `LIMIT/OFFSET`, mais simples para CLI e API. Para tabelas
  grandes, a paginação por chave (keyset) é mais eficiente.
- A regra das 40 horas semanais é aplicada pela aplicação. Outro cliente que escreva direto no
  banco não passa por ela.
- No livro, Jorge Brito aparece no projeto 20 com horas nulas. Como `horas` é `NOT NULL` aqui, essa
  linha foi omitida dos dados de exemplo.
- Não há autenticação na API.
