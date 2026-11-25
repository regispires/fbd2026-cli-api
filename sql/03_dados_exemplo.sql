-- Dados de exemplo do esquema EMPRESA (Elmasri e Navathe, edição em português).
--
-- Departamentos e projetos recebem como id os números do livro (OVERRIDING
-- SYSTEM VALUE), para que os exemplos das aulas continuem valendo; depois, a
-- sequência de cada IDENTITY é ajustada. Os ids dos funcionários são gerados
-- pelo banco, e as chaves estrangeiras são resolvidas pela chave natural (CPF).
--
-- Os CPFs do livro não têm dígitos verificadores válidos: servem só como dados
-- já cadastrados. Para novos cadastros use CPFs válidos, como 52998224725.
--
-- Fora do livro, há dois registros sem associações, para que as junções
-- externas (LEFT JOIN) tenham o que mostrar: o departamento 6 (Expansão), sem
-- funcionários, projetos nem localização, e o projeto 40 (Portal do Cliente),
-- sem ninguém alocado.

BEGIN;

INSERT INTO departamento (id, dnome) OVERRIDING SYSTEM VALUE VALUES
  (1, 'Matriz'), (4, 'Administração'), (5, 'Pesquisa'),
  (6, 'Expansão');  -- fora do livro: departamento sem associações

SELECT setval(pg_get_serial_sequence('departamento', 'id'),
              (SELECT max(id) FROM departamento));

INSERT INTO funcionario
  (cpf, pnome, minicial, unome, datanasc, endereco, sexo, salario, departamento_id)
VALUES
  ('12345678966', 'João', 'B', 'Silva', '1965-01-09', 'Rua das Flores, 751, São Paulo, SP', 'M', 30000, 5),
  ('33344555587', 'Fernando', 'T', 'Wong', '1955-12-08', 'Rua da Lapa, 34, São Paulo, SP', 'M', 40000, 5),
  ('99988777767', 'Alice', 'J', 'Zelaya', '1968-01-19', 'Rua Souza Lima, 35, Curitiba, PR', 'F', 25000, 4),
  ('98765432168', 'Jennifer', 'S', 'Souza', '1941-06-20', 'Av. Arthur de Lima, 54, Santo André, SP', 'F', 43000, 4),
  ('66688444476', 'Ronaldo', 'K', 'Lima', '1962-09-15', 'Rua Rebouças, 65, Piracicaba, SP', 'M', 38000, 5),
  ('45345345376', 'Joice', 'A', 'Leite', '1972-07-31', 'Av. Lucas Obes, 74, São Paulo, SP', 'F', 25000, 5),
  ('98798798733', 'André', 'V', 'Pereira', '1969-03-29', 'Rua Timbira, 35, São Paulo, SP', 'M', 25000, 4),
  ('88866555576', 'Jorge', 'E', 'Brito', '1937-11-10', 'Rua das Hortênsias, 35, Mauá, SP', 'M', 55000, 1);

-- supervisores: o id de cada lado é encontrado pelo CPF
UPDATE funcionario f
   SET supervisor_id = s.id
  FROM (VALUES ('12345678966', '33344555587'),
               ('33344555587', '88866555576'),
               ('99988777767', '98765432168'),
               ('98765432168', '88866555576'),
               ('66688444476', '33344555587'),
               ('45345345376', '33344555587'),
               ('98798798733', '98765432168')) AS v(cpf, cpf_supervisor)
  JOIN funcionario s ON s.cpf = v.cpf_supervisor
 WHERE f.cpf = v.cpf;

UPDATE departamento d
   SET gerente_id = f.id, data_inicio_gerente = v.inicio::date
  FROM (VALUES (5, '33344555587', '1988-05-22'),
               (4, '98765432168', '1995-01-01'),
               (1, '88866555576', '1981-06-19')) AS v(dep, cpf, inicio)
  JOIN funcionario f ON f.cpf = v.cpf
 WHERE d.id = v.dep;

INSERT INTO localizacoes_dep (departamento_id, dlocal) VALUES
  (1, 'São Paulo'), (4, 'Mauá'), (5, 'Santo André'), (5, 'Itu'), (5, 'São Paulo');

INSERT INTO projeto (id, projnome, projlocal, departamento_id) OVERRIDING SYSTEM VALUE VALUES
  (1, 'ProdutoX', 'Santo André', 5),
  (2, 'ProdutoY', 'Itu', 5),
  (3, 'ProdutoZ', 'São Paulo', 5),
  (10, 'Informatização', 'Mauá', 4),
  (20, 'Reorganização', 'São Paulo', 1),
  (30, 'Novosbenefícios', 'Mauá', 4),
  (40, 'Portal do Cliente', 'São Paulo', 1);  -- fora do livro: sem alocações

SELECT setval(pg_get_serial_sequence('projeto', 'id'),
              (SELECT max(id) FROM projeto));

-- no livro, Jorge aparece no projeto 20 com horas nulas; aqui horas é NOT NULL,
-- então essa linha foi omitida
INSERT INTO trabalha_em (funcionario_id, projeto_id, horas)
SELECT f.id, v.projeto, v.horas
  FROM (VALUES ('12345678966', 1, 32.5), ('12345678966', 2, 7.5),
               ('66688444476', 3, 40.0),
               ('45345345376', 1, 20.0), ('45345345376', 2, 20.0),
               ('33344555587', 2, 10.0), ('33344555587', 3, 10.0),
               ('33344555587', 10, 10.0), ('33344555587', 20, 10.0),
               ('99988777767', 30, 30.0), ('99988777767', 10, 10.0),
               ('98798798733', 10, 35.0), ('98798798733', 30, 5.0),
               ('98765432168', 30, 20.0), ('98765432168', 20, 15.0))
       AS v(cpf, projeto, horas)
  JOIN funcionario f ON f.cpf = v.cpf;

INSERT INTO dependente (funcionario_id, nome_dependente, sexo, datanasc, parentesco)
SELECT f.id, v.nome, v.sexo, v.nascimento::date, v.parentesco
  FROM (VALUES ('33344555587', 'Alícia', 'F', '1986-04-05', 'Filha'),
               ('33344555587', 'Tiago', 'M', '1983-10-25', 'Filho'),
               ('33344555587', 'Janaína', 'F', '1958-05-03', 'Esposa'),
               ('98765432168', 'Antônio', 'M', '1942-02-28', 'Marido'),
               ('12345678966', 'Michael', 'M', '1988-01-04', 'Filho'),
               ('12345678966', 'Alícia', 'F', '1988-12-30', 'Filha'),
               ('12345678966', 'Elizabeth', 'F', '1967-05-05', 'Esposa'))
       AS v(cpf, nome, sexo, nascimento, parentesco)
  JOIN funcionario f ON f.cpf = v.cpf;

COMMIT;
