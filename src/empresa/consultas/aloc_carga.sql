SELECT COALESCE(SUM(horas), 0)
  FROM trabalha_em
 WHERE fcpf = %(cpf)s
