DELETE FROM funcionario
 WHERE id = %(id)s
RETURNING id
