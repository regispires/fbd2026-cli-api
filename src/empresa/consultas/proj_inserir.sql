-- id é IDENTITY: o banco gera o valor e o devolve
INSERT INTO projeto (projnome, projlocal, departamento_id)
VALUES (%(projnome)s, %(projlocal)s, %(departamento_id)s)
RETURNING id, projnome, projlocal, departamento_id
