SELECT dnumero, dnome, cpf_gerente, data_inicio_gerente
  FROM departamento
 WHERE dnumero = %(dnumero)s
