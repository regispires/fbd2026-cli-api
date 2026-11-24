-- projnumero é IDENTITY: o banco gera o valor e o devolve
INSERT INTO projeto (projnome, projlocal, dnum)
VALUES (%(projnome)s, %(projlocal)s, %(dnum)s)
RETURNING projnumero, projnome, projlocal, dnum
