UPDATE departamento
   SET dnome = %(dnome)s
 WHERE id = %(id)s
RETURNING id, dnome, gerente_id, data_inicio_gerente
