SELECT id, dnome, gerente_id, data_inicio_gerente
  FROM departamento
 WHERE id = %(id)s
