DELETE FROM trabalha_em
 WHERE funcionario_id = %(funcionario_id)s
   AND projeto_id = %(projeto_id)s
RETURNING funcionario_id
