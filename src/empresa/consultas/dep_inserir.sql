INSERT INTO departamento (dnumero, dnome)
VALUES (%(dnumero)s, %(dnome)s)
RETURNING dnumero, dnome, cpf_gerente, data_inicio_gerente
