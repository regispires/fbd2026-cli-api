-- trava a linha do funcionário até o fim da transação
SELECT cpf
  FROM funcionario
 WHERE cpf = %(cpf)s
   FOR UPDATE
