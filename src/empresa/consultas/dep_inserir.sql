-- id é IDENTITY: o banco gera o valor e o devolve
INSERT INTO departamento (dnome)
VALUES (%(dnome)s)
RETURNING id, dnome, gerente_id, data_inicio_gerente
