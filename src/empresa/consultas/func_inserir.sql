INSERT INTO funcionario (cpf, pnome, minicial, unome, datanasc, endereco,
                         sexo, salario, cpf_supervisor, dnr)
VALUES (%(cpf)s, %(pnome)s, %(minicial)s, %(unome)s, %(datanasc)s, %(endereco)s,
        %(sexo)s, %(salario)s, %(cpf_supervisor)s, %(dnr)s)
RETURNING cpf, pnome, minicial, unome, datanasc, endereco,
          sexo, salario, cpf_supervisor, dnr
