DELETE FROM departamento
 WHERE id = %(id)s
RETURNING id
