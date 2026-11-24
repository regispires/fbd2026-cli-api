UPDATE departamento
   SET cpf_gerente = %(cpf)s,
       data_inicio_gerente = CURRENT_DATE
 WHERE dnumero = %(dnumero)s
