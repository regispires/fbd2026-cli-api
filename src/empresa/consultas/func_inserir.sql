-- id é IDENTITY: o banco gera o valor e o devolve
INSERT INTO funcionario (cpf, pnome, minicial, unome, datanasc, endereco,
                         sexo, salario, supervisor_id, departamento_id)
VALUES (%(cpf)s, %(pnome)s, %(minicial)s, %(unome)s, %(datanasc)s, %(endereco)s,
        %(sexo)s, %(salario)s, %(supervisor_id)s, %(departamento_id)s)
RETURNING id, cpf, pnome, minicial, unome, datanasc, endereco,
          sexo, salario, supervisor_id, departamento_id
