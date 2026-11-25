SELECT id, projnome, projlocal, departamento_id
  FROM projeto
 WHERE departamento_id = %(departamento_id)s
 ORDER BY id
