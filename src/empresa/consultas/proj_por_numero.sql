SELECT projnumero, projnome, projlocal, dnum
  FROM projeto
 WHERE projnumero = %(projnumero)s
