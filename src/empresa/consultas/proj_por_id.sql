SELECT id, projnome, projlocal, departamento_id
  FROM projeto
 WHERE id = %(id)s
