SELECT projnumero, projnome, projlocal, dnum
  FROM projeto
 WHERE dnum = %(dnum)s
 ORDER BY projnumero
