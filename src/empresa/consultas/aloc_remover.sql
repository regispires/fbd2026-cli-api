DELETE FROM trabalha_em
 WHERE fcpf = %(cpf)s
   AND pnr = %(projnumero)s
RETURNING fcpf
