UPDATE departamento
   SET gerente_id = %(gerente_id)s,
       data_inicio_gerente = CURRENT_DATE
 WHERE id = %(id)s
