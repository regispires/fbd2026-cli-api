SELECT id, cpf, pnome, minicial, unome, datanasc,
       endereco, sexo, salario, supervisor_id,
       departamento_id
  FROM funcionario
 WHERE id = %(id)s
