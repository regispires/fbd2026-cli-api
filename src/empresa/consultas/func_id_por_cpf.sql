-- converte a chave natural (CPF) na chave substituta (id)
SELECT id
  FROM funcionario
 WHERE cpf = %(cpf)s
