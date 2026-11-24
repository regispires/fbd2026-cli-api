DELETE FROM funcionario
 WHERE cpf = %(cpf)s
RETURNING cpf
