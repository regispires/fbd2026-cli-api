-- trava a linha do funcionário até o fim da transação
SELECT id
  FROM funcionario
 WHERE id = %(id)s
   FOR UPDATE
