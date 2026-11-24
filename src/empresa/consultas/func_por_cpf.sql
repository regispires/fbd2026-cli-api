SELECT cpf, pnome, minicial, unome, datanasc,
       endereco, sexo, salario, cpf_supervisor,
       dnr
  FROM funcionario
 WHERE cpf = %(cpf)s
