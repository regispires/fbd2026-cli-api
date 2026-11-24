DELETE FROM projeto
 WHERE projnumero = %(projnumero)s
RETURNING projnumero
