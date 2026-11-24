-- Dados de exemplo do esquema EMPRESA (Elmasri e Navathe, edição em português).
-- Os CPFs do livro não têm dígitos verificadores válidos: servem só como dados
-- já cadastrados. Para novos cadastros use CPFs válidos, como 52998224725.

BEGIN;

-- a FK funcionario -> departamento é verificada só no COMMIT
SET CONSTRAINTS fk_func_dep DEFERRED;

INSERT INTO funcionario
  (cpf, pnome, minicial, unome, datanasc, endereco, sexo, salario, cpf_supervisor, dnr)
VALUES
  ('88866555576', 'Jorge', 'E', 'Brito', '1937-11-10', 'Rua das Hortênsias, 35, Mauá, SP', 'M', 55000, NULL, 1),
  ('98765432168', 'Jennifer', 'S', 'Souza', '1941-06-20', 'Av. Arthur de Lima, 54, Santo André, SP', 'F', 43000, '88866555576', 4),
  ('33344555587', 'Fernando', 'T', 'Wong', '1955-12-08', 'Rua da Lapa, 34, São Paulo, SP', 'M', 40000, '88866555576', 5),
  ('12345678966', 'João', 'B', 'Silva', '1965-01-09', 'Rua das Flores, 751, São Paulo, SP', 'M', 30000, '33344555587', 5),
  ('99988777767', 'Alice', 'J', 'Zelaya', '1968-01-19', 'Rua Souza Lima, 35, Curitiba, PR', 'F', 25000, '98765432168', 4),
  ('66688444476', 'Ronaldo', 'K', 'Lima', '1962-09-15', 'Rua Rebouças, 65, Piracicaba, SP', 'M', 38000, '33344555587', 5),
  ('45345345376', 'Joice', 'A', 'Leite', '1972-07-31', 'Av. Lucas Obes, 74, São Paulo, SP', 'F', 25000, '33344555587', 5),
  ('98798798733', 'André', 'V', 'Pereira', '1969-03-29', 'Rua Timbira, 35, São Paulo, SP', 'M', 25000, '98765432168', 4);

INSERT INTO departamento (dnumero, dnome, cpf_gerente, data_inicio_gerente) VALUES
  (5, 'Pesquisa', '33344555587', '1988-05-22'),
  (4, 'Administração', '98765432168', '1995-01-01'),
  (1, 'Matriz', '88866555576', '1981-06-19');

INSERT INTO localizacoes_dep (dnumero, dlocal) VALUES
  (1, 'São Paulo'), (4, 'Mauá'), (5, 'Santo André'), (5, 'Itu'), (5, 'São Paulo');

INSERT INTO projeto (projnumero, projnome, projlocal, dnum) VALUES
  (1, 'ProdutoX', 'Santo André', 5),
  (2, 'ProdutoY', 'Itu', 5),
  (3, 'ProdutoZ', 'São Paulo', 5),
  (10, 'Informatização', 'Mauá', 4),
  (20, 'Reorganização', 'São Paulo', 1),
  (30, 'Novosbenefícios', 'Mauá', 4);

-- valores explícitos não avançam a IDENTITY: ajusta a sequência
SELECT setval(pg_get_serial_sequence('projeto', 'projnumero'),
              (SELECT max(projnumero) FROM projeto));

-- no livro, Jorge aparece no projeto 20 com horas nulas; aqui horas é NOT NULL,
-- então essa linha foi omitida
INSERT INTO trabalha_em (fcpf, pnr, horas) VALUES
  ('12345678966', 1, 32.5), ('12345678966', 2, 7.5),
  ('66688444476', 3, 40.0),
  ('45345345376', 1, 20.0), ('45345345376', 2, 20.0),
  ('33344555587', 2, 10.0), ('33344555587', 3, 10.0),
  ('33344555587', 10, 10.0), ('33344555587', 20, 10.0),
  ('99988777767', 30, 30.0), ('99988777767', 10, 10.0),
  ('98798798733', 10, 35.0), ('98798798733', 30, 5.0),
  ('98765432168', 30, 20.0), ('98765432168', 20, 15.0);

INSERT INTO dependente (fcpf, nome_dependente, sexo, datanasc, parentesco) VALUES
  ('33344555587', 'Alícia', 'F', '1986-04-05', 'Filha'),
  ('33344555587', 'Tiago', 'M', '1983-10-25', 'Filho'),
  ('33344555587', 'Janaína', 'F', '1958-05-03', 'Esposa'),
  ('98765432168', 'Antônio', 'M', '1942-02-28', 'Marido'),
  ('12345678966', 'Michael', 'M', '1988-01-04', 'Filho'),
  ('12345678966', 'Alícia', 'F', '1988-12-30', 'Filha'),
  ('12345678966', 'Elizabeth', 'F', '1967-05-05', 'Esposa');

COMMIT;
