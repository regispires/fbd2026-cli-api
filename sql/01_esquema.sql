-- Esquema EMPRESA (adaptado de Elmasri e Navathe)
-- Chaves primárias substitutas (id IDENTITY) nas entidades principais; as chaves
-- naturais continuam como UNIQUE NOT NULL. Restrições nomeadas: a aplicação
-- traduz cada violação em mensagem de domínio.

CREATE TABLE departamento (
  id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  dnome               VARCHAR(30) NOT NULL,
  gerente_id          BIGINT,
  data_inicio_gerente DATE,
  CONSTRAINT uq_dep_nome UNIQUE (dnome)
);

CREATE TABLE funcionario (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  cpf             CHAR(11) NOT NULL,
  pnome           VARCHAR(15) NOT NULL,
  minicial        CHAR(1),
  unome           VARCHAR(15) NOT NULL,
  datanasc        DATE,
  endereco        VARCHAR(60),
  sexo            CHAR(1),
  salario         NUMERIC(10,2) NOT NULL,
  supervisor_id   BIGINT,
  departamento_id BIGINT,
  CONSTRAINT uq_func_cpf UNIQUE (cpf),
  CONSTRAINT ck_func_cpf CHECK (cpf ~ '^[0-9]{11}$'),
  CONSTRAINT ck_func_sexo CHECK (sexo IN ('M', 'F')),
  CONSTRAINT ck_func_salario CHECK (salario > 0),
  CONSTRAINT ck_func_superv CHECK (supervisor_id <> id),
  CONSTRAINT fk_func_superv FOREIGN KEY (supervisor_id)
    REFERENCES funcionario (id) ON DELETE SET NULL,
  -- ciclo funcionario <-> departamento: FK adiável para cargas em uma transação
  CONSTRAINT fk_func_dep FOREIGN KEY (departamento_id)
    REFERENCES departamento (id) DEFERRABLE INITIALLY IMMEDIATE
);

ALTER TABLE departamento
  ADD CONSTRAINT fk_dep_gerente FOREIGN KEY (gerente_id)
  REFERENCES funcionario (id);

CREATE TABLE projeto (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  projnome        VARCHAR(30) NOT NULL,
  projlocal       VARCHAR(30),
  departamento_id BIGINT NOT NULL,
  CONSTRAINT uq_proj_nome UNIQUE (projnome),
  CONSTRAINT fk_proj_dep FOREIGN KEY (departamento_id)
    REFERENCES departamento (id)
);

-- associativa: a chave composta já identifica a linha
CREATE TABLE trabalha_em (
  funcionario_id BIGINT NOT NULL,
  projeto_id     BIGINT NOT NULL,
  horas          NUMERIC(4,1) NOT NULL,
  CONSTRAINT pk_trabalha_em PRIMARY KEY (funcionario_id, projeto_id),
  CONSTRAINT ck_te_horas CHECK (horas > 0),
  CONSTRAINT fk_te_func FOREIGN KEY (funcionario_id)
    REFERENCES funcionario (id),
  CONSTRAINT fk_te_proj FOREIGN KEY (projeto_id)
    REFERENCES projeto (id)
);

-- atributo multivalorado: nunca referenciado, chave composta
CREATE TABLE localizacoes_dep (
  departamento_id BIGINT NOT NULL,
  dlocal          VARCHAR(30) NOT NULL,
  CONSTRAINT pk_localizacoes_dep PRIMARY KEY (departamento_id, dlocal),
  CONSTRAINT fk_loc_dep FOREIGN KEY (departamento_id)
    REFERENCES departamento (id) ON DELETE CASCADE
);

CREATE TABLE dependente (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  funcionario_id  BIGINT NOT NULL,
  nome_dependente VARCHAR(30) NOT NULL,
  sexo            CHAR(1),
  datanasc        DATE,
  parentesco      VARCHAR(15),
  CONSTRAINT uq_dependente UNIQUE (funcionario_id, nome_dependente),
  CONSTRAINT fk_dep_func FOREIGN KEY (funcionario_id)
    REFERENCES funcionario (id) ON DELETE CASCADE
);

-- índices para FKs, filtros e ordenações usados pela aplicação
CREATE INDEX ix_func_superv ON funcionario (supervisor_id);
CREATE INDEX ix_func_dep_nome ON funcionario (departamento_id, unome, id);
CREATE INDEX ix_dep_gerente ON departamento (gerente_id);
CREATE INDEX ix_proj_dep ON projeto (departamento_id);
CREATE INDEX ix_te_proj ON trabalha_em (projeto_id);
