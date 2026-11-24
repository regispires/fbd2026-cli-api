UPDATE departamento
   SET dnome = %(dnome)s
 WHERE dnumero = %(dnumero)s
RETURNING dnumero, dnome, cpf_gerente, data_inicio_gerente
