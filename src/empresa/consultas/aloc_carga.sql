SELECT COALESCE(SUM(horas), 0)
  FROM trabalha_em
 WHERE funcionario_id = %(funcionario_id)s
