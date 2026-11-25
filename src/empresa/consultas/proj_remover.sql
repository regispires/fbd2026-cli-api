DELETE FROM projeto
 WHERE id = %(id)s
RETURNING id
